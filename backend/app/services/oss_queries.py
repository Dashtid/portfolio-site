"""GraphQL query + variable builders for the admin OSS contribution dashboard.

The query covers the upstream repos we track for OSS contributions and
returns enough per-PR signal for the bucket classifier to discriminate
NOW vs WAITING without a second round-trip. The tracked list is sharded
(``shard_tracked_repos``) so it can outgrow GitHub's 256-char search
limit; the sync service runs the query once per shard. Cost ~4 GraphQL
points per shard per refresh against a 5000 pts/hour limit —
thousands-fold headroom even at several shards.

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
    "Efferent-Health/fo-dicom.Codecs",
)
"""The 9 upstream repos covered by the dashboard. v1.3 will auto-discover.

INVARIANT: every entry MUST be a public repository accessible to a PAT
scoped only to ``public_repo``. Private / archived / renamed repos
return empty GraphQL search results without raising, which silently
hides that repo from the dashboard. The unit-test allowlist mirror in
``tests/test_oss_schemas.py`` is the contract: adding a repo here
requires updating the test in the same change so a private entry
can't slip in.

This list is also a SECURITY CONTROL, not just scope: it is what keeps
private / IP-tainted repos out of the searches whose results feed a
public surface. Never replace it with a bare ``author:`` search.

Since 2026-08-29 the list is sharded (``shard_tracked_repos``) and the
sync service runs the query once per shard, so adding a repo here no
longer risks the 256-char search limit — the first 8 repos already sat
at 255/256.
"""

SEARCH_QUERY_MAX_LEN: int = 256
"""GitHub's documented search-query length limit (chars).

See https://docs.github.com/en/search-github/searching-on-github/troubleshooting-search-queries.
Queries over this length are rejected with ``Validation failed``. The
guard in ``build_dashboard_variables`` asserts every generated string
stays under this limit so a 9th tracked repo can't silently break the
dashboard in production.
"""

LATER_ITEMS: tuple[dict[str, str], ...] = ()
"""Hardcoded queued future-work items for the LATER bucket.

LATER is intentionally out of GraphQL — these are things Dashtid plans
to file/upstream but hasn't yet. Each entry is a small dict with
``title`` and optional ``description`` / ``url`` fields; the endpoint
merges them into the LATER bucket in the GET response.

Empty for v1; add entries inline when there's queued work worth
surfacing on the dashboard (or move to a ``queued/`` folder in the
oss-contributions tracker repo if the list grows past ~5).
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


def _search_strings(username: str, cutoff: str, repo_clause: str) -> dict[str, str]:
    """The five search strings, in one place.

    ``build_dashboard_variables`` fills these for real, and
    ``shard_tracked_repos`` measures them with an empty repo clause to learn
    the per-shard character budget — sharing the templates is what stops the
    packer's budget from silently drifting when a template is edited.

    ``closed:>=`` filters by close date AND implies ``is:closed``, saving
    ~10 chars vs ``is:closed updated:>=``; the trade-off is missing the rare
    long-closed thread that gets a recent comment — noise for an
    operational DONE bucket anyway.
    """

    return {
        "authoredOpenPRs": f"author:{username} is:pr is:open {repo_clause}",
        "authoredOpenIssues": f"author:{username} is:issue is:open {repo_clause}",
        "authoredClosed": f"author:{username} closed:>={cutoff} {repo_clause}",
        "commentedOpen": f"commenter:{username} -author:{username} is:open {repo_clause}",
        "commentedClosed": (
            f"commenter:{username} -author:{username} closed:>={cutoff} {repo_clause}"
        ),
    }


def shard_tracked_repos(
    repos: tuple[str, ...] = TRACKED_REPOS,
    *,
    username: str = GITHUB_USERNAME,
) -> tuple[tuple[str, ...], ...]:
    """Split ``repos`` into groups whose search strings all fit GitHub's limit.

    The sync service runs ``OSS_DASHBOARD_QUERY`` once per shard and merges
    the results, so the tracked list can grow past what a single 256-char
    search can hold (the original 8 repos measured 255/256; the 9th made a
    single query impossible). Greedy first-fit in declaration order: order
    is stable, every repo lands in exactly one shard, and each extra shard
    costs one more GraphQL request (~4 rate-limit points against 5000/hour).

    The budget is derived from the LONGEST template with the clause empty —
    the cutoff is an ISO date, so a fixed placeholder measures identically.
    A single repo name too long for a whole shard of its own gets a
    one-repo shard anyway; ``build_dashboard_variables`` then raises its
    loud ValueError rather than this function guessing.
    """

    budget = SEARCH_QUERY_MAX_LEN - max(
        len(s) for s in _search_strings(username, "0000-00-00", "").values()
    )

    shards: list[tuple[str, ...]] = []
    current: list[str] = []
    used = 0
    for repo in repos:
        cost = len(f"repo:{repo}") + (1 if current else 0)
        if current and used + cost > budget:
            shards.append(tuple(current))
            current = []
            used = 0
            cost = len(f"repo:{repo}")
        current.append(repo)
        used += cost
    if current:
        shards.append(tuple(current))
    return tuple(shards)


def build_dashboard_variables(
    *,
    repos: tuple[str, ...],
    username: str = GITHUB_USERNAME,
    as_of: datetime | None = None,
    window_days: int = DONE_WINDOW_DAYS,
    first: int = DEFAULT_SEARCH_LIMIT,
) -> dict[str, str | int]:
    """Build the 5 search-query strings + paging limit for ``OSS_DASHBOARD_QUERY``.

    ``repos`` is required and should be ONE shard from
    ``shard_tracked_repos()`` — the full TRACKED_REPOS stopped fitting a
    single query at 9 entries (it had no default precisely so nobody can
    reach for the old single-query habit and hit the runtime guard).

    Pass ``as_of`` to pin the DONE-bucket window for deterministic tests;
    production calls leave it None so the window slides with wall-clock time.
    """

    now = as_of if as_of is not None else datetime.now(UTC)
    cutoff = (now - timedelta(days=window_days)).date().isoformat()
    searches = _search_strings(username, cutoff, _repo_filter(repos))

    # Callers are expected to pass ONE SHARD from shard_tracked_repos();
    # the full 9-repo TRACKED_REPOS no longer fits a single query. This
    # guard stays as the last line of defence for a pathological shard
    # (e.g. a single repo name that alone blows the budget).
    for key, value in searches.items():
        if len(value) > SEARCH_QUERY_MAX_LEN:
            raise ValueError(
                f"OSS dashboard search '{key}' is {len(value)} chars, "
                f"over GitHub's {SEARCH_QUERY_MAX_LEN}-char limit. "
                f"Callers must pass a shard from shard_tracked_repos(), "
                f"not the full TRACKED_REPOS."
            )

    return {**searches, "first": first}


MERGE_INFO_PREVIEW_ACCEPT: str = "application/vnd.github.merge-info-preview+json"
"""Accept header required by GitHub to populate ``mergeStateStatus`` on a PR.

Configure on the githubkit GitHub() client so every GraphQL POST in the
dashboard service carries it. Without the header GitHub returns null for
``mergeStateStatus`` — the schema tolerates that, but the NOW-bucket
``rebase needed`` signal is lost.
"""
