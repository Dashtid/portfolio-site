"""Pure-function bucket classifier for the admin OSS contribution dashboard.

Maps a GraphQL response node (PR or Issue) onto one of the four
GitHub-derived buckets:

- ``NOW``     — open PR by Dashtid awaiting *his* action
- ``WAITING`` — open PR by Dashtid awaiting *maintainer* action
- ``WATCHING``— open Issue by Dashtid OR open thread he commented on substantively
- ``DONE``    — merged PR, closed Issue, or thread he commented on that is now closed

LATER lives outside GraphQL (hardcoded queued work) and is merged into
the GET response at serve time — not produced here.

The classifier is pure (no I/O, no DB, no settings reads) so the test
suite can exercise every branch with cheap fixture nodes.
"""

import logging
from enum import Enum
from typing import assert_never

from app.schemas.oss import (
    CheckStatusState,
    CommentsConnection,
    IssueNode,
    MergeStateStatus,
    PullRequestLite,
    PullRequestNode,
    PullRequestState,
    ReviewDecision,
)
from app.services.oss_queries import COMMENT_BOT_ALLOWLIST

logger = logging.getLogger(__name__)

SUBSTANTIVE_COMMENT_MIN_CHARS: int = 80
"""Threshold for the WATCHING-bucket substantive-vs-drive-by heuristic."""

# Author-action merge-state-statuses. Anything in this set means Dashtid
# needs to do something (resolve conflicts, rebase, fix hooks) before a
# maintainer can merge.
_AUTHOR_ACTION_MERGE_STATES: frozenset[MergeStateStatus] = frozenset(
    {
        MergeStateStatus.DIRTY,
        MergeStateStatus.BEHIND,
        MergeStateStatus.UNSTABLE,
        MergeStateStatus.HAS_HOOKS,
    }
)

# CI rollup states that indicate the author broke something.
_AUTHOR_ACTION_CHECK_STATES: frozenset[CheckStatusState] = frozenset(
    {
        CheckStatusState.FAILURE,
        CheckStatusState.ERROR,
    }
)


class Bucket(str, Enum):
    """The 5 dashboard buckets. ``LATER`` is hardcoded; never produced here."""

    NOW = "NOW"
    WAITING = "WAITING"
    WATCHING = "WATCHING"
    LATER = "LATER"
    DONE = "DONE"


class Source(str, Enum):
    """Which top-level search alias produced the node.

    Knowing the source lets the classifier short-circuit branches —
    e.g. a node from ``commentedClosed`` is always DONE-on-others,
    never a PR Dashtid authored.
    """

    AUTHORED_OPEN_PRS = "authoredOpenPRs"
    AUTHORED_OPEN_ISSUES = "authoredOpenIssues"
    AUTHORED_CLOSED = "authoredClosed"
    COMMENTED_OPEN = "commentedOpen"
    COMMENTED_CLOSED = "commentedClosed"


def _has_substantive_dashtid_comment(
    comments: CommentsConnection | None,
    *,
    username: str,
) -> bool:
    """True if Dashtid's last 5 comments include one >= the char threshold.

    Whitespace is stripped before measuring length so a 100-space comment
    doesn't game the heuristic. The bot allowlist is consulted as
    defense-in-depth: the ``author.login == username`` check already
    excludes bots today, but encoding the allowlist makes the design
    intent enforced rather than incidental.
    """

    if comments is None:
        return False
    return any(
        c.author is not None
        and c.author.login == username
        and c.author.login not in COMMENT_BOT_ALLOWLIST
        and c.body_text is not None
        and len(c.body_text.strip()) >= SUBSTANTIVE_COMMENT_MIN_CHARS
        for c in comments.nodes
    )


def _is_authored_by(
    node: PullRequestNode | PullRequestLite | IssueNode,
    username: str,
) -> bool:
    """Defensive guard: AUTHORED-source nodes must actually have ``username``
    as ``author.login``. If a future query-string swap accidentally puts
    commented-on threads into an AUTHORED bucket, this catches it before
    the node is mis-bucketed.
    """

    return node.author is not None and node.author.login == username


def _classify_authored_open_pr(pr: PullRequestNode) -> Bucket:
    """Discriminate NOW vs WAITING on an open PR Dashtid authored."""

    # Drafts haven't been promoted to review-requested yet — Dashtid's
    # call. Treat as NOW so the dashboard surfaces them as actionable.
    if pr.is_draft:
        return Bucket.NOW

    # Reviewer explicitly asked for changes -> author's court.
    if pr.review_decision == ReviewDecision.CHANGES_REQUESTED:
        return Bucket.NOW

    # CI is broken -> author's court.
    head_rollup = pr.commits.nodes[0].commit.status_check_rollup if pr.commits.nodes else None
    if head_rollup is not None and head_rollup.state in _AUTHOR_ACTION_CHECK_STATES:
        return Bucket.NOW

    # Branch is behind base / has conflicts / failing required hooks ->
    # author's court. ``BLOCKED`` is excluded because that's typically
    # branch-protection waiting on a maintainer review or check.
    if pr.merge_state_status in _AUTHOR_ACTION_MERGE_STATES:
        return Bucket.NOW

    # Otherwise the ball is in the maintainer's court.
    return Bucket.WAITING


def classify(  # noqa: PLR0911, PLR0912 — match-case dispatcher; collapsing branches would hide intent
    node: PullRequestNode | PullRequestLite | IssueNode,
    *,
    source: Source,
    username: str,
) -> Bucket | None:
    """Map a GraphQL node to a bucket, or None to drop it from the dashboard.

    ``username`` is passed in so tests can sweep both branches; in production
    it's always ``oss_queries.GITHUB_USERNAME``.

    Returns ``None`` for nodes that don't meet the bucket's threshold —
    e.g. a drive-by single-character comment Dashtid left on someone
    else's PR that the substantive-comment heuristic rejects.
    """

    match source:
        case Source.AUTHORED_OPEN_PRS:
            # By construction the search returned an open PR Dashtid authored.
            if not isinstance(node, PullRequestNode):
                return None
            if node.state != PullRequestState.OPEN:
                return None
            if not _is_authored_by(node, username):
                logger.warning(
                    "OSS classifier dropped non-%s-authored node from %s",
                    username,
                    source.value,
                    extra={"node_id": node.id},
                )
                return None
            return _classify_authored_open_pr(node)

        case Source.AUTHORED_OPEN_ISSUES:
            # Open Issues Dashtid authored — always WATCHING.
            if not isinstance(node, IssueNode):
                return None
            if not _is_authored_by(node, username):
                logger.warning(
                    "OSS classifier dropped non-%s-authored node from %s",
                    username,
                    source.value,
                    extra={"node_id": node.id},
                )
                return None
            return Bucket.WATCHING

        case Source.AUTHORED_CLOSED:
            # Anything Dashtid authored that has closed -> DONE.
            if not _is_authored_by(node, username):
                logger.warning(
                    "OSS classifier dropped non-%s-authored node from %s",
                    username,
                    source.value,
                    extra={"node_id": node.id},
                )
                return None
            return Bucket.DONE

        case Source.COMMENTED_OPEN:
            # Threads Dashtid commented on. Apply the substantive-comment
            # heuristic — drive-by reactions don't earn a slot.
            if not _has_substantive_dashtid_comment(
                getattr(node, "comments", None), username=username
            ):
                return None
            return Bucket.WATCHING

        case Source.COMMENTED_CLOSED:
            # Same substantive filter, but the thread is closed -> DONE.
            if not _has_substantive_dashtid_comment(
                getattr(node, "comments", None), username=username
            ):
                return None
            return Bucket.DONE

        case _:
            # Python match-case is non-exhaustive by default; the assert_never
            # call turns a forgotten Source value into a loud runtime failure
            # AND a static-exhaustiveness anchor mypy can verify.
            assert_never(source)
