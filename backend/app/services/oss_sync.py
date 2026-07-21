"""Async refresh-orchestrator for the admin OSS contribution dashboard.

One module = one shared ``OssSyncService`` singleton wired into the
FastAPI lifespan. The service owns:

- the long-lived ``githubkit.GitHub`` async client (must be used inside
  an ``async with`` block to avoid the OpenSSL CA-bundle leak documented
  in githubkit issue #285);
- the in-process refresh-in-progress lock so a stampede of POST /refresh
  calls collapses to one upstream fetch;
- the pure-function pipeline that maps a GraphQL response onto a list
  of ``OssContribution`` rows for upsert.

``refresh()`` is the only state-mutating method. It runs the GraphQL
query, walks each search alias through the classifier, replaces every
row in ``oss_contributions`` inside a single transaction, and returns
an ``OssRefreshResult`` carrying the rate-limit cost so the admin
endpoint can surface it to the dashboard.

LATER bucket items live in ``oss_queries.LATER_ITEMS``; the sync path
ignores them entirely (they're not GraphQL-derived). The endpoint
merges them into the GET response at serve time.
"""

import asyncio
import contextlib
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any, cast

from githubkit import GitHub
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.oss import OssContribution
from app.schemas.oss import (
    IssueNode,
    OssDashboardResponse,
    OssRefreshResult,
    PullRequestLite,
    PullRequestNode,
)
from app.services.bucket_classifier import Bucket, Source, classify
from app.services.oss_queries import (
    GITHUB_USERNAME,
    OSS_DASHBOARD_QUERY,
    build_dashboard_variables,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ``previews=['merge-info']`` resolves to the
# ``application/vnd.github.merge-info-preview+json`` Accept header that
# GitHub requires to populate ``mergeStateStatus``. Without it the field
# returns null and the NOW-bucket ``BEHIND/DIRTY`` discriminator is lost.
_GITHUB_PREVIEWS: tuple[str, ...] = ("merge-info",)


class OssSyncError(RuntimeError):
    """Raised when a refresh fails before the DB transaction starts.

    The endpoint converts this into a 502 (generic upstream failure) or
    a 503 (when ``is_pat_missing`` is True, signalling a configuration
    problem the operator can fix).

    The ``is_pat_missing`` boolean replaces the brittle "search for
    a substring in str(exc)" pattern the endpoint used to use — the
    error message is allowed to evolve without breaking routing.
    """

    def __init__(self, message: str, *, is_pat_missing: bool = False) -> None:
        super().__init__(message)
        self.is_pat_missing = is_pat_missing


def _sanitize_pat(text: str) -> str:
    """Redact the configured PAT (if any) from a string.

    githubkit / httpx exceptions can include header dumps that contain
    ``Authorization: Bearer <token>`` — if we don't scrub the text
    before logging it, the PAT lands in stdout and Sentry. Returning
    the same string when no PAT is configured keeps the helper safe in
    tests where ``settings.GITHUB_OSS_DASHBOARD_PAT`` is None.
    """

    pat = settings.GITHUB_OSS_DASHBOARD_PAT
    if not pat:
        return text
    return text.replace(pat, "***REDACTED***")


class OssSyncService:
    """Refresh orchestrator. Singleton per process; wired in main.lifespan."""

    def __init__(self) -> None:
        # Lazily constructed so settings.GITHUB_OSS_DASHBOARD_PAT can be
        # absent in tests / dev without crashing at import time.
        self._refresh_lock: asyncio.Lock = asyncio.Lock()
        self._refresh_in_progress: bool = False

    @property
    def refresh_in_progress(self) -> bool:
        """Cheap flag the admin endpoint surfaces so the UI can disable
        the refresh button while a sync is running.
        """

        return self._refresh_in_progress

    @contextlib.asynccontextmanager
    async def _github_client(self) -> AsyncIterator[GitHub]:
        """Yield a configured ``GitHub`` async client.

        The ``async with`` lifecycle is mandatory: without it githubkit
        constructs a fresh ``httpx.AsyncClient`` per request which leaks
        the OpenSSL CA bundle into native heap (~16 MB / 20 calls per
        upstream issue #285). At our 6h cadence that would OOM a 512 MB
        Fly Machine inside a week.
        """

        token = settings.GITHUB_OSS_DASHBOARD_PAT
        if not token:
            raise OssSyncError(
                "GITHUB_OSS_DASHBOARD_PAT is not configured. "
                "The OSS dashboard cannot refresh without a public_repo-scoped PAT.",
                is_pat_missing=True,
            )
        async with GitHub(
            token,
            previews=_GITHUB_PREVIEWS,
            user_agent="portfolio-oss-dashboard/0.1",
        ) as client:
            yield client

    async def refresh(self, session: AsyncSession) -> OssRefreshResult:
        """Pull fresh contributions from GitHub, classify, replace the table.

        Stampede-protected: concurrent callers serialize on the refresh
        lock so a manual-refresh button-mash doesn't fan out into
        multiple upstream pulls.
        """

        async with self._refresh_lock:
            self._refresh_in_progress = True
            try:
                payload = await self._fetch_payload()
            finally:
                # Release the in-progress flag before the DB write so the
                # admin endpoint shows progress only during the network
                # call, not during the (much faster) DB swap.
                self._refresh_in_progress = False

            response = OssDashboardResponse.model_validate(payload)

            # Log the rate-limit cost so Sentry breadcrumbs and structured
            # logs carry the telemetry without a separate DB table.
            logger.info(
                "OSS dashboard refresh fetched",
                extra={
                    "rate_limit_cost": response.rate_limit.cost,
                    "rate_limit_remaining": response.rate_limit.remaining,
                    "rate_limit_reset_at": response.rate_limit.reset_at.isoformat(),
                    "node_count": response.rate_limit.node_count,
                },
            )

            rows = list(self._classify_response(response))

            # Replace-with-history transaction (D3-FEAT-01): the operational
            # buckets are replaced wholesale, but merged self-authored PRs
            # are PERMANENT public evidence — the homepage Open Source strip
            # reads them via /api/v1/oss/contributions, and the GraphQL
            # searches only cover a 30-day closed window, so a plain
            # delete-all would silently erase every older merged PR from
            # the public surface on the first refresh. Keep merged history;
            # upsert incoming rows over it by github_node_id.
            merged_history = (
                (OssContribution.kind == "pr")
                & (OssContribution.state == "MERGED")
                & (OssContribution.author_login == GITHUB_USERNAME)
            )
            await session.execute(delete(OssContribution).where(~merged_history))

            preserved = {
                row.github_node_id: row
                for row in ((await session.execute(select(OssContribution))).scalars().all())
            }
            for row in rows:
                existing = preserved.get(row.github_node_id)
                if existing is None:
                    session.add(row)
                    continue
                # Refresh the preserved row in place with the fresh fetch
                for field in (
                    "kind",
                    "repo_name_with_owner",
                    "number",
                    "title",
                    "url",
                    "state",
                    "is_draft",
                    "author_login",
                    "bucket",
                    "created_at",
                    "last_activity_at",
                    "closed_at",
                    "merged_at",
                    "synced_at",
                ):
                    setattr(existing, field, getattr(row, field))
            await session.commit()

            return OssRefreshResult(
                contributions_count=len(rows),
                rate_limit_cost=response.rate_limit.cost,
                rate_limit_remaining=response.rate_limit.remaining,
                finished_at=datetime.now(UTC),
            )

    async def _fetch_payload(self) -> dict[str, Any]:
        """Execute the GraphQL query and return the raw ``data`` envelope.

        githubkit's ``graphql.arequest()`` returns ``dict[str, Any]``
        (the unwrapped ``data`` field). We hand it to Pydantic next.
        """

        variables = build_dashboard_variables()
        async with self._github_client() as client:
            try:
                return await client.graphql.arequest(OSS_DASHBOARD_QUERY, variables)
            except Exception as exc:
                # NEVER use ``logger.exception`` (auto-attaches exc_info /
                # full traceback) nor leak the raw exception via the chain.
                # githubkit + httpx historically embed Authorization-header
                # values in error reprs; the configured PAT would land
                # unredacted in stdout and Sentry. Sanitize both the log
                # message and the chained-exception traceback (``from None``
                # drops __cause__ so downstream handlers can't re-derive it).
                sanitized = _sanitize_pat(f"{type(exc).__name__}: {exc}")
                logger.error("OSS dashboard GraphQL fetch failed: %s", sanitized)
                raise OssSyncError(f"GitHub GraphQL fetch failed: {sanitized}") from None

    @staticmethod
    def _classify_response(
        response: OssDashboardResponse,
    ) -> list[OssContribution]:
        """Walk every search alias, classify each node, return model rows.

        Pure function — kept separate from ``refresh()`` so tests can
        exercise the classification fan-out against fixture responses
        without spinning up an event loop or a DB.
        """

        rows: list[OssContribution] = []

        def emit(
            node: PullRequestNode | PullRequestLite | IssueNode,
            *,
            source: Source,
        ) -> None:
            bucket = classify(node, source=source, username=GITHUB_USERNAME)
            if bucket is None:
                return
            rows.append(_node_to_row(node, bucket=bucket))

        for pr in response.authored_open_prs.nodes:
            emit(pr, source=Source.AUTHORED_OPEN_PRS)
        for issue in response.authored_open_issues.nodes:
            emit(issue, source=Source.AUTHORED_OPEN_ISSUES)
        for mixed in response.authored_closed.nodes:
            emit(mixed, source=Source.AUTHORED_CLOSED)
        for commented in response.commented_open.nodes:
            emit(commented, source=Source.COMMENTED_OPEN)
        for closed in response.commented_closed.nodes:
            emit(closed, source=Source.COMMENTED_CLOSED)

        # De-duplicate by github_node_id, keeping the FIRST occurrence.
        # The five aliases above run in this order: AUTHORED_OPEN_PRS,
        # AUTHORED_OPEN_ISSUES, AUTHORED_CLOSED, COMMENTED_OPEN,
        # COMMENTED_CLOSED. The current GraphQL queries already exclude
        # self-authored via ``-author:{username}`` on the commented_*
        # searches, so collisions can't happen today — but the iteration
        # order makes the authored variant win if a future query change
        # ever drops the exclusion, which is the right priority (the
        # authored row carries the richer NOW/WAITING signals).
        deduped: dict[str, OssContribution] = {}
        for row in rows:
            deduped.setdefault(
                cast("str", row.github_node_id),
                row,
            )
        return list(deduped.values())


def _node_to_row(
    node: PullRequestNode | PullRequestLite | IssueNode,
    *,
    bucket: Bucket,
) -> OssContribution:
    """Map a GraphQL node onto an ``OssContribution`` model row."""

    if isinstance(node, IssueNode):
        kind = "issue"
        merged_at: datetime | None = None
        is_draft = False
    else:
        kind = "pr"
        merged_at = node.merged_at
        # PullRequestLite has no is_draft field; assume False.
        is_draft = getattr(node, "is_draft", False)

    return OssContribution(
        id=str(uuid.uuid4()),
        github_node_id=node.id,
        kind=kind,
        repo_name_with_owner=node.repository.name_with_owner,
        number=node.number,
        title=node.title,
        url=node.url,
        state=node.state.value,
        is_draft=is_draft,
        author_login=node.author.login if node.author else None,
        bucket=bucket.value,
        created_at=node.created_at,
        last_activity_at=node.updated_at,
        closed_at=node.closed_at,
        merged_at=merged_at,
    )


# Module-level singleton — wired into the FastAPI lifespan and injected
# into the admin endpoint via app.state. Constructed lazily because
# constructing the GitHub() client requires a PAT that tests don't set.
oss_sync_service = OssSyncService()
