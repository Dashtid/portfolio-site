# mypy: disable-error-code=call-arg

"""Pure-function tests for the OSS bucket classifier.

Targets ≥95% line coverage on ``app.services.bucket_classifier`` per the
NOTES.md Phase 4 mandate — the classifier is the operational heart of
the dashboard, so it needs the tightest test net.

Fixtures construct minimal valid GraphQL nodes by editing the on-disk
JSON fixture so we don't reinvent shape details; the schemas validate
each variant.

The Pydantic v2 mypy plugin checks ``call-arg`` against field aliases
only, even when ``populate_by_name=True`` makes the snake_case field
names valid at runtime. We use snake_case throughout this file for
readability; the file-level disable above suppresses the false
positives without weakening type-checking elsewhere.
"""

import copy
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.schemas.oss import (
    Actor,
    CheckStatusState,
    CommentsConnection,
    CommentStub,
    CommitNode,
    CommitsConnection,
    CommitStub,
    IssueNode,
    IssueState,
    MergeableState,
    MergeStateStatus,
    OssDashboardResponse,
    PullRequestLite,
    PullRequestNode,
    PullRequestState,
    RepoStub,
    ReviewDecision,
    ReviewsConnection,
    StatusCheckRollup,
)
from app.services.bucket_classifier import (
    SUBSTANTIVE_COMMENT_MIN_CHARS,
    Bucket,
    Source,
    classify,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "oss_dashboard_response.json"
USERNAME = "Dashtid"


@pytest.fixture
def parsed_fixture() -> OssDashboardResponse:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fh:
        return OssDashboardResponse.model_validate(json.load(fh))


def _base_pr_node(**overrides) -> PullRequestNode:
    """Build a minimal-but-valid PullRequestNode for classifier branch testing."""

    defaults: dict = {
        "typename": "PullRequest",
        "id": "PR_test",
        "number": 1,
        "title": "t",
        "url": "https://example.com",
        "state": PullRequestState.OPEN,
        "is_draft": False,
        "merged": False,
        "merged_at": None,
        "closed_at": None,
        "created_at": datetime(2026, 6, 1, tzinfo=UTC),
        "updated_at": datetime(2026, 6, 10, tzinfo=UTC),
        "author": Actor(login=USERNAME),
        "repository": RepoStub(name_with_owner="anchore/syft"),
        "mergeable": MergeableState.MERGEABLE,
        "merge_state_status": MergeStateStatus.CLEAN,
        "review_decision": ReviewDecision.REVIEW_REQUIRED,
        "commits": CommitsConnection(
            nodes=[
                CommitNode(
                    commit=CommitStub(
                        oid="deadbeef",
                        status_check_rollup=StatusCheckRollup(state=CheckStatusState.SUCCESS),
                    )
                )
            ]
        ),
        "reviews": ReviewsConnection(total_count=0, nodes=[]),
        "comments": CommentsConnection(total_count=0, nodes=[]),
    }
    defaults.update(overrides)
    return PullRequestNode(**defaults)


def _base_issue_node(**overrides) -> IssueNode:
    defaults: dict = {
        "typename": "Issue",
        "id": "I_test",
        "number": 2,
        "title": "i",
        "url": "https://example.com",
        "state": IssueState.OPEN,
        "state_reason": None,
        "created_at": datetime(2026, 5, 20, tzinfo=UTC),
        "updated_at": datetime(2026, 6, 1, tzinfo=UTC),
        "closed_at": None,
        "author": Actor(login=USERNAME),
        "repository": RepoStub(name_with_owner="anchore/grype"),
        "comments": None,
    }
    defaults.update(overrides)
    return IssueNode(**defaults)


class TestAuthoredOpenPRsClassification:
    """NOW vs WAITING discrimination on PRs Dashtid authored."""

    def test_changes_requested_review_is_now(self):
        pr = _base_pr_node(review_decision=ReviewDecision.CHANGES_REQUESTED)
        assert classify(pr, source=Source.AUTHORED_OPEN_PRS, username=USERNAME) == Bucket.NOW

    def test_failed_ci_is_now(self):
        pr = _base_pr_node(
            commits=CommitsConnection(
                nodes=[
                    CommitNode(
                        commit=CommitStub(
                            oid="x",
                            status_check_rollup=StatusCheckRollup(state=CheckStatusState.FAILURE),
                        )
                    )
                ]
            ),
        )
        assert classify(pr, source=Source.AUTHORED_OPEN_PRS, username=USERNAME) == Bucket.NOW

    def test_errored_ci_is_now(self):
        pr = _base_pr_node(
            commits=CommitsConnection(
                nodes=[
                    CommitNode(
                        commit=CommitStub(
                            oid="x",
                            status_check_rollup=StatusCheckRollup(state=CheckStatusState.ERROR),
                        )
                    )
                ]
            ),
        )
        assert classify(pr, source=Source.AUTHORED_OPEN_PRS, username=USERNAME) == Bucket.NOW

    @pytest.mark.parametrize(
        "merge_state",
        [
            MergeStateStatus.DIRTY,
            MergeStateStatus.BEHIND,
            MergeStateStatus.UNSTABLE,
            MergeStateStatus.HAS_HOOKS,
        ],
    )
    def test_author_action_merge_states_are_now(self, merge_state: MergeStateStatus):
        pr = _base_pr_node(merge_state_status=merge_state)
        assert classify(pr, source=Source.AUTHORED_OPEN_PRS, username=USERNAME) == Bucket.NOW

    def test_draft_is_now(self):
        pr = _base_pr_node(is_draft=True)
        assert classify(pr, source=Source.AUTHORED_OPEN_PRS, username=USERNAME) == Bucket.NOW

    def test_clean_open_pr_with_review_required_is_waiting(self):
        pr = _base_pr_node()
        assert classify(pr, source=Source.AUTHORED_OPEN_PRS, username=USERNAME) == Bucket.WAITING

    def test_approved_clean_pr_is_waiting(self):
        """APPROVED but not yet merged -> maintainer's court."""
        pr = _base_pr_node(review_decision=ReviewDecision.APPROVED)
        assert classify(pr, source=Source.AUTHORED_OPEN_PRS, username=USERNAME) == Bucket.WAITING

    def test_blocked_state_alone_is_waiting(self):
        """BLOCKED typically means branch-protection — maintainer review missing."""
        pr = _base_pr_node(merge_state_status=MergeStateStatus.BLOCKED)
        assert classify(pr, source=Source.AUTHORED_OPEN_PRS, username=USERNAME) == Bucket.WAITING

    def test_unknown_merge_state_is_waiting(self):
        pr = _base_pr_node(merge_state_status=MergeStateStatus.UNKNOWN)
        assert classify(pr, source=Source.AUTHORED_OPEN_PRS, username=USERNAME) == Bucket.WAITING

    def test_empty_commits_no_rollup_is_waiting(self):
        pr = _base_pr_node(commits=CommitsConnection(nodes=[]))
        assert classify(pr, source=Source.AUTHORED_OPEN_PRS, username=USERNAME) == Bucket.WAITING

    def test_closed_pr_under_open_source_is_dropped(self):
        """Defensive: search syntax shouldn't return closed PRs here, but the
        classifier must not bucket one if it slips through."""
        pr = _base_pr_node(state=PullRequestState.MERGED)
        assert classify(pr, source=Source.AUTHORED_OPEN_PRS, username=USERNAME) is None

    def test_issue_node_under_pr_source_is_dropped(self):
        issue = _base_issue_node()
        assert classify(issue, source=Source.AUTHORED_OPEN_PRS, username=USERNAME) is None


class TestAuthoredOpenIssuesClassification:
    def test_open_issue_is_watching(self):
        issue = _base_issue_node()
        assert (
            classify(issue, source=Source.AUTHORED_OPEN_ISSUES, username=USERNAME)
            == Bucket.WATCHING
        )

    def test_pull_request_under_issue_source_is_dropped(self):
        pr = _base_pr_node()
        assert classify(pr, source=Source.AUTHORED_OPEN_ISSUES, username=USERNAME) is None


class TestAuthoredClosedClassification:
    def test_merged_pr_is_done(self):
        pr = _base_pr_node(state=PullRequestState.MERGED, merged=True)
        assert classify(pr, source=Source.AUTHORED_CLOSED, username=USERNAME) == Bucket.DONE

    def test_closed_issue_is_done(self):
        issue = _base_issue_node(state=IssueState.CLOSED)
        assert classify(issue, source=Source.AUTHORED_CLOSED, username=USERNAME) == Bucket.DONE


class TestCommentedOpenClassification:
    def test_substantive_comment_promotes_to_watching(self):
        issue = _base_issue_node(
            author=Actor(login="someone-else"),
            comments=CommentsConnection(
                total_count=1,
                nodes=[
                    CommentStub(
                        author=Actor(login=USERNAME),
                        created_at=datetime(2026, 6, 1, tzinfo=UTC),
                        body_text="x" * (SUBSTANTIVE_COMMENT_MIN_CHARS + 1),
                    )
                ],
            ),
        )
        assert classify(issue, source=Source.COMMENTED_OPEN, username=USERNAME) == Bucket.WATCHING

    def test_drive_by_short_comment_is_dropped(self):
        issue = _base_issue_node(
            author=Actor(login="someone-else"),
            comments=CommentsConnection(
                total_count=1,
                nodes=[
                    CommentStub(
                        author=Actor(login=USERNAME),
                        created_at=datetime(2026, 6, 1, tzinfo=UTC),
                        body_text="lgtm",
                    )
                ],
            ),
        )
        assert classify(issue, source=Source.COMMENTED_OPEN, username=USERNAME) is None

    def test_no_comments_field_is_dropped(self):
        issue = _base_issue_node(author=Actor(login="someone-else"), comments=None)
        assert classify(issue, source=Source.COMMENTED_OPEN, username=USERNAME) is None

    def test_comments_by_other_users_only_are_dropped(self):
        """Only Dashtid's own substantive comment counts."""
        issue = _base_issue_node(
            author=Actor(login="someone-else"),
            comments=CommentsConnection(
                total_count=1,
                nodes=[
                    CommentStub(
                        author=Actor(login="some-maintainer"),
                        created_at=datetime(2026, 6, 1, tzinfo=UTC),
                        body_text="x" * (SUBSTANTIVE_COMMENT_MIN_CHARS + 1),
                    )
                ],
            ),
        )
        assert classify(issue, source=Source.COMMENTED_OPEN, username=USERNAME) is None

    def test_pull_request_lite_with_substantive_comment_promotes(self):
        pr_lite = PullRequestLite(
            typename="PullRequest",
            id="PR_lite",
            number=5,
            title="t",
            url="https://example.com",
            state=PullRequestState.OPEN,
            merged=False,
            merged_at=None,
            closed_at=None,
            created_at=datetime(2026, 5, 1, tzinfo=UTC),
            updated_at=datetime(2026, 6, 1, tzinfo=UTC),
            author=Actor(login="someone-else"),
            repository=RepoStub(name_with_owner="anchore/syft"),
            comments=CommentsConnection(
                total_count=1,
                nodes=[
                    CommentStub(
                        author=Actor(login=USERNAME),
                        created_at=datetime(2026, 6, 1, tzinfo=UTC),
                        body_text="x" * (SUBSTANTIVE_COMMENT_MIN_CHARS + 1),
                    )
                ],
            ),
        )
        assert classify(pr_lite, source=Source.COMMENTED_OPEN, username=USERNAME) == Bucket.WATCHING


class TestCommentedClosedClassification:
    def test_substantive_comment_on_closed_thread_is_done(self):
        issue = _base_issue_node(
            state=IssueState.CLOSED,
            author=Actor(login="someone-else"),
            comments=CommentsConnection(
                total_count=1,
                nodes=[
                    CommentStub(
                        author=Actor(login=USERNAME),
                        created_at=datetime(2026, 5, 20, tzinfo=UTC),
                        body_text="x" * (SUBSTANTIVE_COMMENT_MIN_CHARS + 1),
                    )
                ],
            ),
        )
        assert classify(issue, source=Source.COMMENTED_CLOSED, username=USERNAME) == Bucket.DONE

    def test_drive_by_on_closed_thread_is_dropped(self):
        issue = _base_issue_node(
            state=IssueState.CLOSED,
            author=Actor(login="someone-else"),
            comments=CommentsConnection(
                total_count=1,
                nodes=[
                    CommentStub(
                        author=Actor(login=USERNAME),
                        created_at=datetime(2026, 5, 20, tzinfo=UTC),
                        body_text="ok",
                    )
                ],
            ),
        )
        assert classify(issue, source=Source.COMMENTED_CLOSED, username=USERNAME) is None


class TestClassifierOnFixture:
    """End-to-end sanity check on the full fixture payload."""

    def test_fixture_authored_open_prs_split_now_vs_waiting(
        self, parsed_fixture: OssDashboardResponse
    ):
        """The fixture's two open PRs cover NOW (DefectDojo) and WAITING (syft)."""
        results = [
            classify(pr, source=Source.AUTHORED_OPEN_PRS, username=USERNAME)
            for pr in parsed_fixture.authored_open_prs.nodes
        ]
        assert results == [Bucket.NOW, Bucket.WAITING]

    def test_fixture_authored_open_issue_is_watching(self, parsed_fixture: OssDashboardResponse):
        results = [
            classify(issue, source=Source.AUTHORED_OPEN_ISSUES, username=USERNAME)
            for issue in parsed_fixture.authored_open_issues.nodes
        ]
        assert results == [Bucket.WATCHING]

    def test_fixture_authored_closed_all_done(self, parsed_fixture: OssDashboardResponse):
        results = [
            classify(node, source=Source.AUTHORED_CLOSED, username=USERNAME)
            for node in parsed_fixture.authored_closed.nodes
        ]
        assert all(r == Bucket.DONE for r in results)

    def test_fixture_commented_closed_with_substantive_dashtid_comment_is_done(
        self, parsed_fixture: OssDashboardResponse
    ):
        results = [
            classify(node, source=Source.COMMENTED_CLOSED, username=USERNAME)
            for node in parsed_fixture.commented_closed.nodes
        ]
        assert results == [Bucket.DONE]


class TestClassifierIdempotence:
    """Defensive sanity: classifying twice gives the same answer."""

    def test_repeated_calls_consistent(self):
        pr = _base_pr_node(review_decision=ReviewDecision.CHANGES_REQUESTED)
        first = classify(pr, source=Source.AUTHORED_OPEN_PRS, username=USERNAME)
        second = classify(pr, source=Source.AUTHORED_OPEN_PRS, username=USERNAME)
        assert first is second is Bucket.NOW

    def test_does_not_mutate_input_node(self):
        pr = _base_pr_node(review_decision=ReviewDecision.CHANGES_REQUESTED)
        before = copy.deepcopy(pr)
        classify(pr, source=Source.AUTHORED_OPEN_PRS, username=USERNAME)
        # Pydantic models support equality comparison field-by-field.
        assert pr == before


class TestAuthorGuardOnAuthoredSources:
    """A non-Dashtid-authored node tagged as AUTHORED_* must be dropped.

    Defensive: a hypothetical query-string swap or fixture mistake would
    otherwise let commented-on threads slip into the authored buckets.
    """

    def test_non_dashtid_pr_under_authored_open_prs_is_dropped(self):
        pr = _base_pr_node(author=Actor(login="someone-else"))
        assert classify(pr, source=Source.AUTHORED_OPEN_PRS, username=USERNAME) is None

    def test_non_dashtid_issue_under_authored_open_issues_is_dropped(self):
        issue = _base_issue_node(author=Actor(login="someone-else"))
        assert classify(issue, source=Source.AUTHORED_OPEN_ISSUES, username=USERNAME) is None

    def test_non_dashtid_pr_under_authored_closed_is_dropped(self):
        pr = _base_pr_node(
            author=Actor(login="someone-else"),
            state=PullRequestState.MERGED,
            merged=True,
        )
        assert classify(pr, source=Source.AUTHORED_CLOSED, username=USERNAME) is None

    def test_null_author_under_authored_source_is_dropped(self):
        """GitHub ghost-user threads: author can be None on very old rows."""
        pr = _base_pr_node(author=None)
        assert classify(pr, source=Source.AUTHORED_OPEN_PRS, username=USERNAME) is None


class TestSubstantiveCommentEdgeCases:
    """Whitespace, length boundary, and bot-allowlist defense-in-depth."""

    def test_whitespace_only_comment_does_not_qualify(self):
        """A comment of 100 spaces passes naive len() but is empty after strip."""
        issue = _base_issue_node(
            author=Actor(login="someone-else"),
            comments=CommentsConnection(
                total_count=1,
                nodes=[
                    CommentStub(
                        author=Actor(login=USERNAME),
                        created_at=datetime(2026, 6, 1, tzinfo=UTC),
                        body_text=" " * (SUBSTANTIVE_COMMENT_MIN_CHARS + 20),
                    )
                ],
            ),
        )
        assert classify(issue, source=Source.COMMENTED_OPEN, username=USERNAME) is None

    def test_comment_at_threshold_qualifies(self):
        """A comment of exactly SUBSTANTIVE_COMMENT_MIN_CHARS non-whitespace passes."""
        issue = _base_issue_node(
            author=Actor(login="someone-else"),
            comments=CommentsConnection(
                total_count=1,
                nodes=[
                    CommentStub(
                        author=Actor(login=USERNAME),
                        created_at=datetime(2026, 6, 1, tzinfo=UTC),
                        body_text="x" * SUBSTANTIVE_COMMENT_MIN_CHARS,
                    )
                ],
            ),
        )
        assert classify(issue, source=Source.COMMENTED_OPEN, username=USERNAME) == Bucket.WATCHING

    def test_comment_one_below_threshold_drops(self):
        issue = _base_issue_node(
            author=Actor(login="someone-else"),
            comments=CommentsConnection(
                total_count=1,
                nodes=[
                    CommentStub(
                        author=Actor(login=USERNAME),
                        created_at=datetime(2026, 6, 1, tzinfo=UTC),
                        body_text="x" * (SUBSTANTIVE_COMMENT_MIN_CHARS - 1),
                    )
                ],
            ),
        )
        assert classify(issue, source=Source.COMMENTED_OPEN, username=USERNAME) is None
