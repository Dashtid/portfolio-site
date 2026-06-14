"""Admin-only HTTP surface for the OSS contribution dashboard.

Two routes:

- ``GET /api/v1/admin/oss`` returns the bucketed contribution view the
  frontend renders. Merges the hardcoded LATER items into the DB rows.
- ``POST /api/v1/admin/oss/refresh`` triggers a fresh GraphQL pull and
  returns the rate-limit telemetry of the refresh.

Both gates on ``get_current_admin_user`` so the data-disclosure surface
(maintainer logins, PAT-derived activity) stays admin-only.
"""

from datetime import UTC, datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.deps import get_current_admin_user
from app.database import get_db
from app.middleware import limiter
from app.models.oss import OssContribution
from app.models.user import User
from app.schemas.oss import OssContributionRow, OssDashboardView, OssRefreshResult
from app.services.bucket_classifier import Bucket
from app.services.oss_queries import LATER_ITEMS, TRACKED_REPOS
from app.services.oss_sync import OssSyncError, oss_sync_service

router = APIRouter()

AdminUser = Annotated[User, Depends(get_current_admin_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]


def _empty_buckets() -> dict[str, list[OssContributionRow]]:
    """Pre-seed every bucket so the UI doesn't have to handle missing keys."""

    return {bucket.value: [] for bucket in Bucket}


def _row_to_dto(row: OssContribution) -> OssContributionRow:
    return OssContributionRow.model_validate(row)


def _later_items_as_rows() -> list[OssContributionRow]:
    """Project the hardcoded LATER tuple onto the row shape.

    Synthetic ID per item (stable for a given title) so the frontend
    can use it as a Vue key without colliding with real DB ids.
    """

    rows: list[OssContributionRow] = []
    fallback_ts = datetime(2026, 1, 1, tzinfo=UTC)
    for item in LATER_ITEMS:
        title = item.get("title", "(untitled)")
        rows.append(
            OssContributionRow(
                id=f"later::{title}",
                kind="later",
                repo_name_with_owner=item.get("repo_name_with_owner", ""),
                number=0,
                title=title,
                url=item.get("url", ""),
                state="LATER",
                is_draft=False,
                author_login=None,
                bucket=Bucket.LATER.value,
                created_at=fallback_ts,
                last_activity_at=fallback_ts,
                closed_at=None,
                merged_at=None,
            )
        )
    return rows


@router.get("/oss", response_model=OssDashboardView)
async def get_oss_dashboard(
    current_user: AdminUser,
    session: DbSession,
) -> OssDashboardView:
    """Return the bucketed contribution view.

    Pure read path — never triggers a refresh. The UI calls
    ``POST /oss/refresh`` to refresh; this lets the dashboard render
    instantly from cached rows while a refresh runs in the background.
    """

    _ = current_user  # admin gate is the sole gate; no per-user data here.

    stmt = select(OssContribution).order_by(
        OssContribution.bucket,
        OssContribution.repo_name_with_owner,
        OssContribution.last_activity_at.desc(),
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()

    buckets = _empty_buckets()
    last_refresh_at: datetime | None = None
    for row in rows:
        bucket_key = cast("str", row.bucket)
        synced_at = cast("datetime", row.synced_at)
        buckets[bucket_key].append(_row_to_dto(row))
        if last_refresh_at is None or synced_at > last_refresh_at:
            last_refresh_at = synced_at

    buckets[Bucket.LATER.value].extend(_later_items_as_rows())

    return OssDashboardView(
        buckets=buckets,
        last_refresh_at=last_refresh_at,
        tracked_repos=TRACKED_REPOS,
        refresh_in_progress=oss_sync_service.refresh_in_progress,
    )


@router.post(
    "/oss/refresh",
    response_model=OssRefreshResult,
    status_code=status.HTTP_200_OK,
)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def refresh_oss_dashboard(
    request: Request,
    current_user: AdminUser,
    session: DbSession,
) -> OssRefreshResult:
    """Pull fresh contribution data from GitHub and replace the cached rows.

    Returns the refresh's rate-limit cost so the dashboard can surface
    how much of the 5000-points/hr budget the run consumed.

    A 502 means GitHub itself failed (rate-limit hit, network error,
    invalid query). A 503 means the PAT is unconfigured server-side —
    actionable by the operator, not the user.

    Rate-limited via ``settings.RATE_LIMIT_AUTH`` (5/minute by default).
    The in-process refresh lock in ``oss_sync_service`` collapses
    concurrent refresh attempts, but rate limiting also guards against
    a sequential button-mash burning the 5000-pts/hour GraphQL budget.
    """

    _ = current_user
    _ = request  # required by slowapi to extract the client identity
    try:
        return await oss_sync_service.refresh(session)
    except OssSyncError as exc:
        if exc.is_pat_missing:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OSS dashboard refresh failed: {exc}",
        ) from exc
