"""Pydantic v2 schemas for the admin OSS contribution dashboard.

These mirror the GraphQL response shape produced by
``app.services.oss_queries.OSS_DASHBOARD_QUERY``. The bucket classifier
(NOW / WAITING / WATCHING / DONE) reads from the parsed response; LATER
is merged in from a hard-coded array server-side and is not modelled here.

Aliases map GitHub's camelCase fields to snake_case attributes; ``extra='ignore'``
keeps the schema forward-compatible if GitHub adds new fields.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class IssueState(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class IssueStateReason(str, Enum):
    COMPLETED = "COMPLETED"
    NOT_PLANNED = "NOT_PLANNED"
    REOPENED = "REOPENED"


class PullRequestState(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    MERGED = "MERGED"


class MergeableState(str, Enum):
    MERGEABLE = "MERGEABLE"
    CONFLICTING = "CONFLICTING"
    UNKNOWN = "UNKNOWN"


class MergeStateStatus(str, Enum):
    CLEAN = "CLEAN"
    DIRTY = "DIRTY"
    BLOCKED = "BLOCKED"
    BEHIND = "BEHIND"
    UNSTABLE = "UNSTABLE"
    HAS_HOOKS = "HAS_HOOKS"
    UNKNOWN = "UNKNOWN"


class ReviewDecision(str, Enum):
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class ReviewState(str, Enum):
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    COMMENTED = "COMMENTED"
    DISMISSED = "DISMISSED"
    PENDING = "PENDING"


class CheckStatusState(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PENDING = "PENDING"
    ERROR = "ERROR"
    EXPECTED = "EXPECTED"


class _OssBase(BaseModel):
    """Shared config: tolerate extra GitHub fields, accept camelCase aliases."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class Actor(_OssBase):
    """GitHub Actor union (User / Bot / Mannequin) — we only need ``login``."""

    login: str


class RepoStub(_OssBase):
    name_with_owner: str = Field(alias="nameWithOwner")
    is_archived: bool = Field(alias="isArchived", default=False)
    is_disabled: bool = Field(alias="isDisabled", default=False)


class StatusCheckRollup(_OssBase):
    state: CheckStatusState | None = None


class CommitStub(_OssBase):
    oid: str
    status_check_rollup: StatusCheckRollup | None = Field(alias="statusCheckRollup", default=None)


class CommitNode(_OssBase):
    commit: CommitStub


class CommitsConnection(_OssBase):
    nodes: list[CommitNode] = Field(default_factory=list)


class ReviewStub(_OssBase):
    state: ReviewState
    submitted_at: datetime | None = Field(alias="submittedAt", default=None)
    author: Actor | None = None


class ReviewsConnection(_OssBase):
    total_count: int = Field(alias="totalCount", default=0)
    nodes: list[ReviewStub] = Field(default_factory=list)


class CommentStub(_OssBase):
    author: Actor | None = None
    created_at: datetime = Field(alias="createdAt")
    body_text: str | None = Field(alias="bodyText", default=None)


class CommentsConnection(_OssBase):
    total_count: int = Field(alias="totalCount", default=0)
    nodes: list[CommentStub] = Field(default_factory=list)


class IssueNode(_OssBase):
    typename: Literal["Issue"] = Field(alias="__typename")
    id: str
    number: int
    title: str
    url: str
    state: IssueState
    state_reason: IssueStateReason | None = Field(alias="stateReason", default=None)
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    closed_at: datetime | None = Field(alias="closedAt", default=None)
    author: Actor | None = None
    repository: RepoStub
    # Only present for results coming from the `commentedOpen` search.
    comments: CommentsConnection | None = None


class PullRequestNode(_OssBase):
    """Full PR shape — used for PRs Dashtid authored.

    Carries every signal the bucket classifier needs to distinguish
    NOW (action on Dashtid) vs WAITING (action on maintainer).
    """

    typename: Literal["PullRequest"] = Field(alias="__typename")
    id: str
    number: int
    title: str
    url: str
    state: PullRequestState
    is_draft: bool = Field(alias="isDraft", default=False)
    merged: bool = False
    merged_at: datetime | None = Field(alias="mergedAt", default=None)
    closed_at: datetime | None = Field(alias="closedAt", default=None)
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    author: Actor | None = None
    repository: RepoStub

    mergeable: MergeableState | None = None
    merge_state_status: MergeStateStatus | None = Field(alias="mergeStateStatus", default=None)
    review_decision: ReviewDecision | None = Field(alias="reviewDecision", default=None)

    commits: CommitsConnection = Field(default_factory=CommitsConnection)
    reviews: ReviewsConnection = Field(default_factory=ReviewsConnection)
    comments: CommentsConnection = Field(default_factory=CommentsConnection)


class PullRequestLite(_OssBase):
    """Lighter PR shape — used for PRs Dashtid only commented on."""

    typename: Literal["PullRequest"] = Field(alias="__typename")
    id: str
    number: int
    title: str
    url: str
    state: PullRequestState
    merged: bool = False
    merged_at: datetime | None = Field(alias="mergedAt", default=None)
    closed_at: datetime | None = Field(alias="closedAt", default=None)
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    author: Actor | None = None
    repository: RepoStub
    comments: CommentsConnection | None = None


# Discriminated unions keyed on __typename — Pydantic v2 picks the right model
# based on the inbound ``__typename`` field of each node.
AuthoredPrNode = PullRequestNode
AuthoredIssueNode = IssueNode
AuthoredMixedNode = PullRequestNode | IssueNode
CommentedNode = PullRequestLite | IssueNode


class AuthoredPrSearchResult(_OssBase):
    """Search result containing only PullRequest nodes (search uses ``is:pr``)."""

    issue_count: int = Field(alias="issueCount", default=0)
    nodes: list[AuthoredPrNode] = Field(default_factory=list)


class AuthoredIssueSearchResult(_OssBase):
    """Search result containing only Issue nodes (search uses ``is:issue``)."""

    issue_count: int = Field(alias="issueCount", default=0)
    nodes: list[AuthoredIssueNode] = Field(default_factory=list)


class AuthoredMixedSearchResult(_OssBase):
    """Search result containing both PullRequest and Issue nodes (no ``is:`` filter)."""

    issue_count: int = Field(alias="issueCount", default=0)
    nodes: list[AuthoredMixedNode] = Field(default_factory=list)


class CommentedSearchResult(_OssBase):
    issue_count: int = Field(alias="issueCount", default=0)
    nodes: list[CommentedNode] = Field(default_factory=list)


class RateLimit(_OssBase):
    cost: int
    remaining: int
    limit: int
    reset_at: datetime = Field(alias="resetAt")
    node_count: int = Field(alias="nodeCount")


class OssDashboardResponse(_OssBase):
    """Top-level GraphQL ``data`` envelope returned by ``githubkit.graphql.arequest``."""

    rate_limit: RateLimit = Field(alias="rateLimit")
    authored_open_prs: AuthoredPrSearchResult = Field(alias="authoredOpenPRs")
    authored_open_issues: AuthoredIssueSearchResult = Field(alias="authoredOpenIssues")
    authored_closed: AuthoredMixedSearchResult = Field(alias="authoredClosed")
    commented_open: CommentedSearchResult = Field(alias="commentedOpen")
    commented_closed: CommentedSearchResult = Field(alias="commentedClosed")
