"""Tests for the admin OSS dashboard Pydantic schemas + query builders.

Validates that:
- A representative GraphQL response fixture round-trips through
  ``OssDashboardResponse`` without raising.
- The discriminated-union nodes (PR vs Issue) get classified by ``__typename``.
- The variable builder produces deterministic search strings for a pinned ``as_of``.
- The bot allowlist + tracked-repos constants are non-empty and immutable.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.schemas.oss import (
    CheckStatusState,
    IssueNode,
    IssueState,
    IssueStateReason,
    MergeStateStatus,
    OssDashboardResponse,
    PullRequestLite,
    PullRequestNode,
    PullRequestState,
    ReviewDecision,
)
from app.services.oss_queries import (
    COMMENT_BOT_ALLOWLIST,
    DEFAULT_SEARCH_LIMIT,
    DONE_WINDOW_DAYS,
    GITHUB_USERNAME,
    OSS_DASHBOARD_QUERY,
    SEARCH_QUERY_MAX_LEN,
    TRACKED_REPOS,
    build_dashboard_variables,
)

# Mirror of TRACKED_REPOS. Any new repo added to production must also be added
# here in the same change, after manually confirming it is a public repo
# accessible to a public_repo-scoped PAT. The PAT cannot reach private repos,
# so a private entry returns empty search results without raising — silently
# hiding the repo from the dashboard.
KNOWN_PUBLIC_REPOS = frozenset(
    {
        "anchore/syft",
        "anchore/grype",
        "anchore/stereoscope",
        "fo-dicom/fo-dicom",
        "pydicom/pydicom",
        "DefectDojo/django-DefectDojo",
        "DependencyTrack/dependency-track",
        "microsoft/presidio",
    }
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "oss_dashboard_response.json"


@pytest.fixture
def fixture_payload() -> dict:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


class TestOssDashboardResponseParsing:
    def test_full_fixture_round_trips(self, fixture_payload: dict):
        response = OssDashboardResponse.model_validate(fixture_payload)
        assert response.rate_limit.cost == 7
        assert response.rate_limit.remaining == 4993
        assert response.rate_limit.limit == 5000

    def test_authored_open_prs_parsed_as_pull_requests(self, fixture_payload: dict):
        response = OssDashboardResponse.model_validate(fixture_payload)
        assert len(response.authored_open_prs.nodes) == 2
        for node in response.authored_open_prs.nodes:
            assert isinstance(node, PullRequestNode)
            assert node.state == PullRequestState.OPEN

    def test_now_signal_fields_present(self, fixture_payload: dict):
        """The NOW-bucket discriminators must survive parsing."""
        response = OssDashboardResponse.model_validate(fixture_payload)
        now_pr = response.authored_open_prs.nodes[0]
        assert now_pr.review_decision == ReviewDecision.CHANGES_REQUESTED
        assert now_pr.merge_state_status == MergeStateStatus.BLOCKED
        assert now_pr.commits.nodes[0].commit.status_check_rollup is not None
        assert now_pr.commits.nodes[0].commit.status_check_rollup.state == CheckStatusState.SUCCESS

    def test_waiting_signal_fields_present(self, fixture_payload: dict):
        response = OssDashboardResponse.model_validate(fixture_payload)
        waiting_pr = response.authored_open_prs.nodes[1]
        assert waiting_pr.review_decision == ReviewDecision.REVIEW_REQUIRED
        assert waiting_pr.merge_state_status == MergeStateStatus.CLEAN
        assert waiting_pr.reviews.total_count == 0

    def test_authored_open_issues_parsed_as_issues(self, fixture_payload: dict):
        response = OssDashboardResponse.model_validate(fixture_payload)
        assert len(response.authored_open_issues.nodes) == 1
        issue = response.authored_open_issues.nodes[0]
        assert isinstance(issue, IssueNode)
        assert issue.state == IssueState.OPEN

    def test_authored_closed_handles_mixed_pr_and_issue(self, fixture_payload: dict):
        response = OssDashboardResponse.model_validate(fixture_payload)
        assert len(response.authored_closed.nodes) == 2
        kinds = {type(n).__name__ for n in response.authored_closed.nodes}
        assert kinds == {"PullRequestNode", "IssueNode"}

    def test_done_issue_state_reason_preserved(self, fixture_payload: dict):
        """``stateReason`` discriminates COMPLETED vs NOT_PLANNED for the UI label."""
        response = OssDashboardResponse.model_validate(fixture_payload)
        closed_nodes = response.authored_closed.nodes
        closed_issue = next(n for n in closed_nodes if isinstance(n, IssueNode))
        assert closed_issue.state == IssueState.CLOSED
        assert closed_issue.state_reason == IssueStateReason.NOT_PLANNED

    def test_commented_open_pulls_comment_bodies(self, fixture_payload: dict):
        """WATCHING-bucket substantive-comment heuristic needs bodyText."""
        response = OssDashboardResponse.model_validate(fixture_payload)
        watching = response.commented_open.nodes[0]
        assert isinstance(watching, IssueNode)
        assert watching.comments is not None
        bodies = [c.body_text for c in watching.comments.nodes]
        assert any(b and len(b) > 80 for b in bodies)
        bot_logins = {c.author.login for c in watching.comments.nodes if c.author}
        assert "github-actions[bot]" in bot_logins

    def test_commented_closed_includes_pull_request_lite(self, fixture_payload: dict):
        response = OssDashboardResponse.model_validate(fixture_payload)
        assert len(response.commented_closed.nodes) == 1
        node = response.commented_closed.nodes[0]
        assert isinstance(node, PullRequestLite)
        assert node.merged is True
        assert node.merged_at == datetime(2026, 5, 30, 14, 0, tzinfo=UTC)


class TestBuildDashboardVariables:
    def test_pinned_as_of_produces_deterministic_strings(self):
        as_of = datetime(2026, 6, 14, 12, 0, tzinfo=UTC)
        variables = build_dashboard_variables(as_of=as_of)

        assert variables["first"] == DEFAULT_SEARCH_LIMIT
        assert "author:Dashtid is:pr is:open" in variables["authoredOpenPRs"]
        assert "author:Dashtid is:issue is:open" in variables["authoredOpenIssues"]
        # 30-day window relative to as_of -> 2026-05-15. We use ``closed:>=``
        # (implies is:closed) instead of ``is:closed updated:>=`` to stay
        # under GitHub's 256-char search-query limit at 8 repos.
        assert "closed:>=2026-05-15" in variables["authoredClosed"]
        assert "closed:>=2026-05-15" in variables["commentedClosed"]
        assert "commenter:Dashtid -author:Dashtid is:open" in variables["commentedOpen"]

    def test_all_8_tracked_repos_appear_in_every_search(self):
        as_of = datetime(2026, 6, 14, 12, 0, tzinfo=UTC)
        variables = build_dashboard_variables(as_of=as_of)
        search_keys = (
            "authoredOpenPRs",
            "authoredOpenIssues",
            "authoredClosed",
            "commentedOpen",
            "commentedClosed",
        )
        for key in search_keys:
            search = variables[key]
            assert isinstance(search, str)
            for repo in TRACKED_REPOS:
                assert f"repo:{repo}" in search, f"{key} missing repo:{repo}"

    def test_custom_window_changes_cutoff(self):
        as_of = datetime(2026, 6, 14, 12, 0, tzinfo=UTC)
        variables = build_dashboard_variables(as_of=as_of, window_days=7)
        assert "closed:>=2026-06-07" in variables["authoredClosed"]

    def test_custom_first_propagates(self):
        as_of = datetime(2026, 6, 14, 12, 0, tzinfo=UTC)
        variables = build_dashboard_variables(as_of=as_of, first=25)
        assert variables["first"] == 25

    def test_search_strings_stay_under_github_256_char_limit(self):
        """GitHub rejects search queries over 256 chars with Validation failed.

        Pin the current lengths so a 9th tracked repo can't silently push
        any search past the limit — the runtime guard raises before sending
        to GitHub, but a CI failure here catches the regression first.
        """
        as_of = datetime(2026, 6, 14, 12, 0, tzinfo=UTC)
        variables = build_dashboard_variables(as_of=as_of)
        for key in (
            "authoredOpenPRs",
            "authoredOpenIssues",
            "authoredClosed",
            "commentedOpen",
            "commentedClosed",
        ):
            value = variables[key]
            assert isinstance(value, str)
            assert len(value) <= SEARCH_QUERY_MAX_LEN, (
                f"{key} is {len(value)} chars, over GitHub's "
                f"{SEARCH_QUERY_MAX_LEN}-char search-query limit"
            )

    def test_oversized_repos_list_raises_loud(self):
        """The runtime guard converts a too-long search into a clear error."""
        as_of = datetime(2026, 6, 14, 12, 0, tzinfo=UTC)
        bloated_repos = TRACKED_REPOS + tuple(
            f"org-{i}/very-long-repository-name-{i}" for i in range(10)
        )
        with pytest.raises(ValueError, match="over GitHub's 256-char limit"):
            build_dashboard_variables(as_of=as_of, repos=bloated_repos)


class TestConstants:
    def test_tracked_repos_immutable_and_complete(self):
        assert isinstance(TRACKED_REPOS, tuple)
        assert len(TRACKED_REPOS) == 8
        # Sanity-check a couple of well-known entries from NOTES.md.
        assert "anchore/syft" in TRACKED_REPOS
        assert "microsoft/presidio" in TRACKED_REPOS

    def test_tracked_repos_match_known_public_allowlist(self):
        """Forces a manual public-visibility check at PR time.

        Production uses a public_repo-scoped PAT; a private/archived entry
        would return empty search results without raising. Adding a repo
        to TRACKED_REPOS without also adding it to ``KNOWN_PUBLIC_REPOS``
        in this test file fails CI, forcing the author to confirm
        visibility before merging.
        """
        repos_set = set(TRACKED_REPOS)
        assert repos_set == KNOWN_PUBLIC_REPOS, (
            f"TRACKED_REPOS drifted from KNOWN_PUBLIC_REPOS allowlist. "
            f"Added without verification: {repos_set - KNOWN_PUBLIC_REPOS}. "
            f"Removed but still allow-listed: {KNOWN_PUBLIC_REPOS - repos_set}."
        )

    def test_tracked_repos_match_owner_name_shape(self):
        """Every entry must be ``owner/name`` with valid GitHub character set."""
        import re

        pattern = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
        for repo in TRACKED_REPOS:
            assert pattern.match(repo), f"{repo!r} is not a valid owner/name"

    def test_bot_allowlist_immutable_and_includes_common_bots(self):
        assert isinstance(COMMENT_BOT_ALLOWLIST, frozenset)
        assert {"github-actions[bot]", "dependabot[bot]", "renovate[bot]"} <= (
            COMMENT_BOT_ALLOWLIST
        )

    def test_query_document_is_self_consistent(self):
        # Sanity-check: the 5 search aliases must appear in the query text or
        # the variable builder will set keys the query doesn't reference.
        for alias in (
            "authoredOpenPRs",
            "authoredOpenIssues",
            "authoredClosed",
            "commentedOpen",
            "commentedClosed",
        ):
            assert f"{alias}:" in OSS_DASHBOARD_QUERY

    def test_username_constant_matches_notes_doc(self):
        assert GITHUB_USERNAME == "Dashtid"

    def test_default_window_is_30_days(self):
        assert DONE_WINDOW_DAYS == 30
