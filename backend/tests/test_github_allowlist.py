"""The project-card allowlist is a security control; these tests are its contract.

``GitHubService.get_portfolio_stats`` feeds the PUBLIC homepage Projects section.
Before ``PUBLIC_REPO_ALLOWLIST`` existed it rendered whatever GitHub returned:
pinned items when the authenticated GraphQL query succeeded, otherwise the six
most recently updated non-fork repos from the REST endpoint. Only ``fork`` was
filtered — no repo-name check of any kind. Two facts made that fail open:

1. The pinned query needs a token. An unset or expired one makes it return an
   empty list rather than raise, so the fallback fires SILENTLY.
2. Archived-but-public repos are still returned by that REST endpoint.

Several repos are deliberately kept off the public portfolio. The allowlist
fails closed instead: a repo renders only if it is named. These tests pin the
set and prove the filter holds on BOTH paths, so a future refactor that drops
it turns CI red rather than publishing a card nobody meant to publish.
"""

from typing import Any

import pytest

from app.services.github_service import PUBLIC_REPO_ALLOWLIST, GitHubService

# Names that must never reach a public project card. Kept as literals rather
# than imported from anywhere: this list is the assertion.
OFF_PORTFOLIO_REPOS = (
    "dicom-fuzzer",
    "sbom-sentinel",
    "medtech-ai-security",
    "defensive-toolkit",
    "offensive-toolkit",
)


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
    def test_allowlist_is_exactly_the_four_public_projects(self) -> None:
        expected = frozenset({"subvectors", "subcheck", "portfolio-site", "sysadmin-toolkit"})
        assert expected == PUBLIC_REPO_ALLOWLIST  # noqa: SIM300 - constant is the contract

    @pytest.mark.parametrize("repo", OFF_PORTFOLIO_REPOS)
    def test_off_portfolio_repos_are_not_allowlisted(self, repo: str) -> None:
        assert repo not in PUBLIC_REPO_ALLOWLIST


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
            pinned=[_pinned("subvectors"), _pinned("offensive-toolkit")],
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
            repos=[_repo(name) for name in (*OFF_PORTFOLIO_REPOS, "subcheck")],
            pinned=[],
        )
        names = {r["name"] for r in stats["featured_repos"]}
        assert names == {"subcheck"}
        for banned in OFF_PORTFOLIO_REPOS:
            assert banned not in names

    @pytest.mark.asyncio
    async def test_fallback_renders_nothing_rather_than_something_unvetted(
        self, service: GitHubService, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Fail closed: no allowlisted repo present -> empty section.
        stats = await self._stats(
            service,
            monkeypatch,
            repos=[_repo(name) for name in OFF_PORTFOLIO_REPOS],
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
