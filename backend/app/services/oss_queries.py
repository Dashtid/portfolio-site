"""GraphQL query + variable builders for the admin OSS contribution dashboard.

The query covers the 8 upstream repos we track for OSS contributions and
returns enough per-PR signal for the bucket classifier to discriminate
NOW vs WAITING without a second round-trip. Cost ~7-8 GraphQL points
per refresh (5 search aliases + nested connections); the 5000 pts/hour
limit is 120,000 pts/day, and 4 refreshes/day burn ~32 pts/day —
~3,750x headroom.

Wire up:
- ``OSS_DASHBOARD_QUERY`` is the static query document; githubkit caches
  the parsed form so the string is hashable + Sentry-breadcrumb readable.
- ``build_dashboard_variables`` returns the 5 search-query strings + paging
  limits; accept an explicit ``as_of`` for deterministic tests.
- ``TRACKED_REPOS`` is the source-of-truth list; bump in code when adding
  a new upstream target (v1.3 auto-discovery is roadmap).
- ``COMMENT_BOT_ALLOWLIST`` is used by the bucket classifier to discount
  drive-by bot noise when deciding if a thread belongs in WATCHING.

The ``mergeStateStatus`` field requires the
``application/vnd.github.merge-info-preview+json`` Accept header on the
GraphQL POST; the service module configures it at the GitHub() client
level. When the header is absent GitHub returns null, which the
Pydantic schema models as ``MergeStateStatus | None``.
"""

from datetime import UTC, datetime, timedelta

# ----------------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------------

GITHUB_USERNAME: str = "Dashtid"
"""The single OSS contributor whose work the dashboard tracks."""

TRACKED_REPOS: tuple[str, ...] = (
    "anchore/syft",
    "anchore/grype",
    "anchore/stereoscope",
    "fo-dicom/fo-dicom",
    "pydicom/pydicom",
    "DefectDojo/django-DefectDojo",
    "DependencyTrack/dependency-track",
    "microsoft/presidio",
)
"""The 8 upstream repos covered by the v1 dashboard. v1.3 will auto-discover.

INVARIANT: every entry MUST be a public repository accessible to a PAT
scoped only to ``public_repo``. Private / archived / renamed repos
return empty GraphQL search results without raising, which silently
hides that repo from the dashboard. The unit-test allowlist mirror in
``tests/test_oss_schemas.py`` is the contract: adding a repo here
requires updating the test in the same change so a private entry
can't slip in.
"""

SEARCH_QUERY_MAX_LEN: int = 256
"""GitHub's documented search-query length limit (chars).

See https://docs.github.com/en/search-github/searching-on-github/troubleshooting-search-queries.
Queries over this length are rejected with ``Validation failed``. The
guard in ``build_dashboard_variables`` asserts every generated string
stays under this limit so a 9th tracked repo can't silently break the
dashboard in production.
"""

DONE_WINDOW_DAYS: int = 30
"""Rolling window for the DONE bucket. Long tail lives in the tracker repo."""

DEFAULT_SEARCH_LIMIT: int = 50
"""Per-search node cap. ~8x headroom over current contribution volume."""

COMMENT_BOT_ALLOWLIST: frozenset[str] = frozenset(
    {
        "github-actions",
        "github-actions[bot]",
        "dependabot",
        "dependabot[bot]",
        "renovate",
        "renovate[bot]",
        "pre-commit-ci",
        "pre-commit-ci[bot]",
        "codecov",
        "codecov[bot]",
        "codecov-commenter",
        "stale",
        "stale[bot]",
        "mergify",
        "mergify[bot]",
        "allcontributors",
        "allcontributors[bot]",
    }
)
"""Bot logins whose comments should NOT count toward the substantive-comment
heuristic in the WATCHING-bucket classifier. Conservative — extend as new
bots show up in maintainer reviews."""


# ----------------------------------------------------------------------------
# GraphQL query
# ----------------------------------------------------------------------------

OSS_DASHBOARD_QUERY: str = """
query OssDashboard(
  $authoredOpenPRs: String!
  $authoredOpenIssues: String!
  $authoredClosed: String!
  $commentedOpen: String!
  $commentedClosed: String!
  $first: Int = 50
) {
  rateLimit { cost remaining limit resetAt nodeCount }

  authoredOpenPRs: search(query: $authoredOpenPRs, type: ISSUE, first: $first) {
    issueCount
    nodes {
      __typename
      ... on PullRequest { ...PrCore }
    }
  }

  authoredOpenIssues: search(query: $authoredOpenIssues, type: ISSUE, first: $first) {
    issueCount
    nodes {
      __typename
      ... on Issue { ...IssueCore }
    }
  }

  authoredClosed: search(query: $authoredClosed, type: ISSUE, first: $first) {
    issueCount
    nodes {
      __typename
      ... on PullRequest { ...PrCore }
      ... on Issue { ...IssueCore }
    }
  }

  commentedOpen: search(query: $commentedOpen, type: ISSUE, first: $first) {
    issueCount
    nodes {
      __typename
      ... on Issue {
        ...IssueCore
        comments(last: 5) {
          totalCount
          nodes { author { login } createdAt bodyText }
        }
      }
      ... on PullRequest {
        ...PrCoreLite
        comments(last: 5) {
          totalCount
          nodes { author { login } createdAt bodyText }
        }
      }
    }
  }

  commentedClosed: search(query: $commentedClosed, type: ISSUE, first: $first) {
    issueCount
    nodes {
      __typename
      ... on Issue { ...IssueCore }
      ... on PullRequest { ...PrCoreLite }
    }
  }
}

fragment RepoStub on Repository { nameWithOwner isArchived isDisabled }

fragment ReviewStub on PullRequestReview {
  state submittedAt author { login }
}

fragment CommitStatus on Commit {
  oid statusCheckRollup { state }
}

fragment PrCore on PullRequest {
  id number title url
  state isDraft merged mergedAt closedAt createdAt updatedAt
  author { login }
  repository { ...RepoStub }
  mergeable mergeStateStatus reviewDecision
  commits(last: 1) { nodes { commit { ...CommitStatus } } }
  reviews(last: 5) { totalCount nodes { ...ReviewStub } }
  comments(last: 3) { totalCount nodes { author { login } createdAt } }
}

fragment PrCoreLite on PullRequest {
  id number title url
  state merged mergedAt closedAt createdAt updatedAt
  author { login }
  repository { ...RepoStub }
}

fragment IssueCore on Issue {
  id number title url
  state stateReason
  closedAt createdAt updatedAt
  author { login }
  repository { ...RepoStub }
}
""".strip()


# ----------------------------------------------------------------------------
# Variable builders
# ----------------------------------------------------------------------------


def _repo_filter(repos: tuple[str, ...]) -> str:
    """Build the ``repo:owner/name`` clauses joined by spaces.

    GitHub's search-syntax treats space-separated ``repo:`` qualifiers as
    OR within the same field, so ``repo:a/b repo:c/d`` matches either repo.
    """

    return " ".join(f"repo:{repo}" for repo in repos)


def build_dashboard_variables(
    *,
    username: str = GITHUB_USERNAME,
    repos: tuple[str, ...] = TRACKED_REPOS,
    as_of: datetime | None = None,
    window_days: int = DONE_WINDOW_DAYS,
    first: int = DEFAULT_SEARCH_LIMIT,
) -> dict[str, str | int]:
    """Build the 5 search-query strings + paging limit for ``OSS_DASHBOARD_QUERY``.

    Pass ``as_of`` to pin the DONE-bucket window for deterministic tests;
    production calls leave it None so the window slides with wall-clock time.
    """

    now = as_of if as_of is not None else datetime.now(UTC)
    cutoff = (now - timedelta(days=window_days)).date().isoformat()
    repo_clause = _repo_filter(repos)

    # ``closed:>=`` filters by close date AND implies ``is:closed``, saving
    # ~10 chars vs ``is:closed updated:>=``. The 256-char search-query limit
    # is tight at 8 repos; the trade-off is that we miss the rare case of a
    # long-closed thread getting a recent Dashtid comment — that signal is
    # noise for an operational DONE bucket anyway.
    searches: dict[str, str] = {
        "authoredOpenPRs": f"author:{username} is:pr is:open {repo_clause}",
        "authoredOpenIssues": f"author:{username} is:issue is:open {repo_clause}",
        "authoredClosed": f"author:{username} closed:>={cutoff} {repo_clause}",
        "commentedOpen": f"commenter:{username} -author:{username} is:open {repo_clause}",
        "commentedClosed": (
            f"commenter:{username} -author:{username} closed:>={cutoff} {repo_clause}"
        ),
    }

    for key, value in searches.items():
        if len(value) > SEARCH_QUERY_MAX_LEN:
            raise ValueError(
                f"OSS dashboard search '{key}' is {len(value)} chars, "
                f"over GitHub's {SEARCH_QUERY_MAX_LEN}-char limit. "
                f"Likely cause: a new entry was added to TRACKED_REPOS. "
                f"Mitigation: split the offending search into multiple "
                f"GraphQL aliases sharded by repo."
            )

    return {**searches, "first": first}


MERGE_INFO_PREVIEW_ACCEPT: str = "application/vnd.github.merge-info-preview+json"
"""Accept header required by GitHub to populate ``mergeStateStatus`` on a PR.

Configure on the githubkit GitHub() client so every GraphQL POST in the
dashboard service carries it. Without the header GitHub returns null for
``mergeStateStatus`` — the schema tolerates that, but the NOW-bucket
``rebase needed`` signal is lost.
"""
