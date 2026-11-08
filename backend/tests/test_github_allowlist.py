"""The project-card allowlist is a security control; these tests are its contract.

``GitHubService.get_portfolio_stats`` feeds the PUBLIC homepage Projects section.
Before ``PUBLIC_REPO_ALLOWLIST`` existed it rendered whatever GitHub returned:
pinned items when the authenticated GraphQL query succeeded, otherwise the six
most recently updated non-fork repos from the REST endpoint. Only ``fork`` was
filtered — no repo-name check of any kind. Two facts made that fail open:

1. The pinned query needs a token. An unset or expired one makes it return an
   empty list rather than raise, so the fallback fires SILENTLY.
2. Archived-but-public repos are still returned by that REST endpoint.

The allowlist fails closed instead: a repo renders only if it is named. These
tests pin the set, check it against the digests of the excluded repository
names, and prove the filter holds on BOTH paths, so a future refactor that
drops it turns CI red rather than publishing a card nobody meant to publish.
"""

from typing import Any

import pytest

from app.services.github_service import PUBLIC_REPO_ALLOWLIST, GitHubService
from tests.hashed_terms import EXCLUDED_REPO_DIGESTS, digest, find

# Names that are on neither list, for the filter tests: the allowlist must drop
# any name it does not carry.
UNLISTED_REPOS = ("unlisted-tool", "archived-notes", "draft-project")


def _repo(name: str) -> dict[str, Any]:
    """A REST-shaped repo record, as ``get_user_repos`` returns them."""
    return {
        "name": name,
        "description": f"{name} description",
        "stargazers_count": 1,
        "forks_count": 0,
        "watchers_count": 1,
        "language": "Python",
        "html_url": f"https://github.com/Dashtid/{name}",
        "fork": False,
    }


def _pinned(name: str) -> dict[str, Any]:
    """A pinned-item record, as ``get_pinned_repos`` returns them."""
    return {
        "name": name,
        "description": f"{name} description",
        "stars": 1,
        "forks": 0,
        "language": "Python",
        "html_url": f"https://github.com/Dashtid/{name}",
    }


class TestAllowlistContents:
    def test_allowlist_is_exactly_the_three_public_projects(self) -> None:
        expected = frozenset({"subvectors", "subcheck", "portfolio-site"})
        assert expected == PUBLIC_REPO_ALLOWLIST  # noqa: SIM300 - constant is the contract

    @pytest.mark.parametrize("repo", sorted(PUBLIC_REPO_ALLOWLIST))
    def test_no_allowlisted_repo_is_an_excluded_name(self, repo: str) -> None:
        assert find(repo, EXCLUDED_REPO_DIGESTS) == []
        assert find(f"https://github.com/Dashtid/{repo}", EXCLUDED_REPO_DIGESTS) == []


class TestExcludedRepoDigests:
    """The digest list and the matcher that reads it."""

    def test_list_holds_five_sha256_digests(self) -> None:
        assert len(EXCLUDED_REPO_DIGESTS) == 5
        assert all(
            len(d) == 64 and set(d) <= set("0123456789abcdef") for d in EXCLUDED_REPO_DIGESTS
        )

    def test_unlisted_names_are_not_on_the_list(self) -> None:
        for name in UNLISTED_REPOS:
            assert digest(name) not in EXCLUDED_REPO_DIGESTS

    @pytest.mark.parametrize(
        "text",
        [
            "example-tool",
            "Example-Tool.",
            "https://github.com/Dashtid/example-tool",
            "git clone git@github.com:Dashtid/example-tool.git",
            '{"full_name": "Dashtid/example-tool"}',
            "the example-tool-docs page",
        ],
    )
    def test_a_listed_name_is_found_in_each_form(self, text: str) -> None:
        digests = EXCLUDED_REPO_DIGESTS | {digest("example-tool")}
        assert find(text, digests) == ["example-tool"]

    def test_a_listed_name_is_not_found_inside_a_longer_word(self) -> None:
        digests = EXCLUDED_REPO_DIGESTS | {digest("example-tool")}
        assert find("example-toolkit, example tool, exampletool", digests) == []


class TestAllowlistIsEnforced:
    """Both code paths must filter — the pinned path AND the silent fallback."""

    @pytest.fixture
    def service(self) -> GitHubService:
        return GitHubService()

    async def _stats(
        self,
        service: GitHubService,
        monkeypatch: pytest.MonkeyPatch,
        *,
        repos: list[dict[str, Any]],
        pinned: list[dict[str, Any]],
    ) -> dict[str, Any]:
        async def fake_user_info(_username: str) -> dict[str, Any]:
            return {"login": "Dashtid", "public_repos": len(repos), "followers": 0}

        async def fake_repos(_username: str, **_kwargs: Any) -> list[dict[str, Any]]:
            return repos

        async def fake_pinned(_username: str) -> list[dict[str, Any]]:
            return pinned

        async def fake_languages(_username: str, _repo: str) -> dict[str, int]:
            return {}

        monkeypatch.setattr(service, "get_user_info", fake_user_info)
        monkeypatch.setattr(service, "get_user_repos", fake_repos)
        monkeypatch.setattr(service, "get_pinned_repos", fake_pinned)
        monkeypatch.setattr(service, "get_repo_languages", fake_languages)
        return await service.get_portfolio_stats("Dashtid")

    @pytest.mark.asyncio
    async def test_pinned_path_drops_non_allowlisted_repos(
        self, service: GitHubService, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A repo pinned by mistake must still not render.
        stats = await self._stats(
            service,
            monkeypatch,
            repos=[_repo("subvectors")],
            pinned=[_pinned("subvectors"), _pinned(UNLISTED_REPOS[0])],
        )
        names = {r["name"] for r in stats["featured_repos"]}
        assert names == {"subvectors"}

    @pytest.mark.asyncio
    async def test_fallback_path_drops_non_allowlisted_repos(
        self, service: GitHubService, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # pinned=[] is the SILENT failure mode (missing/expired token).
        stats = await self._stats(
            service,
            monkeypatch,
            repos=[_repo(name) for name in (*UNLISTED_REPOS, "subcheck")],
            pinned=[],
        )
        names = {r["name"] for r in stats["featured_repos"]}
        assert names == {"subcheck"}
        for unlisted in UNLISTED_REPOS:
            assert unlisted not in names

    @pytest.mark.asyncio
    async def test_fallback_renders_nothing_rather_than_something_unvetted(
        self, service: GitHubService, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Fail closed: no allowlisted repo present -> empty section.
        stats = await self._stats(
            service,
            monkeypatch,
            repos=[_repo(name) for name in UNLISTED_REPOS],
            pinned=[],
        )
        assert stats["featured_repos"] == []

    @pytest.mark.asyncio
    async def test_allowlisted_repos_still_render(
        self, service: GitHubService, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The control must not be so tight it empties the section in normal use.
        stats = await self._stats(
            service,
            monkeypatch,
            repos=[_repo(name) for name in sorted(PUBLIC_REPO_ALLOWLIST)],
            pinned=[],
        )
        assert {r["name"] for r in stats["featured_repos"]} == set(PUBLIC_REPO_ALLOWLIST)
