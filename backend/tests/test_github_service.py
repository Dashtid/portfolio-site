"""
Tests for GitHub service module - initialization, configuration, and API methods
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.github_service import GitHubService, github_service


class TestGitHubServiceInit:
    """Tests for GitHubService initialization."""

    def test_service_init_without_token(self):
        """Test service initialization without GitHub token."""
        with patch("app.services.github_service.settings") as mock_settings:
            mock_settings.GITHUB_TOKEN = None
            service = GitHubService()
            assert service.base_url == "https://api.github.com"
            assert "Authorization" not in service.headers

    def test_service_init_with_token(self):
        """Test service initialization with GitHub token."""
        with patch("app.services.github_service.settings") as mock_settings:
            mock_settings.GITHUB_TOKEN = "test_token_123"
            service = GitHubService()
            assert service.headers["Authorization"] == "token test_token_123"

    def test_service_singleton_exists(self):
        """Test that singleton instance exists."""
        assert github_service is not None
        assert isinstance(github_service, GitHubService)

    def test_service_base_url(self):
        """Test service has correct base URL."""
        service = GitHubService()
        assert service.base_url == "https://api.github.com"

    def test_service_default_headers(self):
        """Test service has default Accept header."""
        service = GitHubService()
        assert service.headers["Accept"] == "application/vnd.github.v3+json"

    def test_service_headers_immutability(self):
        """Test service headers are properly set."""
        service = GitHubService()
        assert "Accept" in service.headers
        assert service.headers["Accept"] == "application/vnd.github.v3+json"

    def test_multiple_service_instances(self):
        """Test that multiple instances can be created."""
        service1 = GitHubService()
        service2 = GitHubService()
        assert service1.base_url == service2.base_url
        assert service1 is not service2

    def test_service_with_empty_token(self):
        """Test service initialization with empty token."""
        with patch("app.services.github_service.settings") as mock_settings:
            mock_settings.GITHUB_TOKEN = ""
            service = GitHubService()
            # Empty string is falsy, so no Authorization header
            assert "Authorization" not in service.headers


class TestGitHubServiceMethodsExist:
    """Tests that GitHub service methods exist and are callable."""

    def test_get_user_info_method_exists(self):
        """Test that get_user_info method exists."""
        service = GitHubService()
        assert hasattr(service, "get_user_info")
        assert callable(service.get_user_info)

    def test_get_user_repos_method_exists(self):
        """Test that get_user_repos method exists."""
        service = GitHubService()
        assert hasattr(service, "get_user_repos")
        assert callable(service.get_user_repos)

    def test_get_repo_details_method_exists(self):
        """Test that get_repo_details method exists."""
        service = GitHubService()
        assert hasattr(service, "get_repo_details")
        assert callable(service.get_repo_details)

    def test_get_repo_languages_method_exists(self):
        """Test that get_repo_languages method exists."""
        service = GitHubService()
        assert hasattr(service, "get_repo_languages")
        assert callable(service.get_repo_languages)

    def test_get_repo_commits_method_exists(self):
        """Test that get_repo_commits method exists."""
        service = GitHubService()
        assert hasattr(service, "get_repo_commits")
        assert callable(service.get_repo_commits)

    def test_get_portfolio_stats_method_exists(self):
        """Test that get_portfolio_stats method exists."""
        service = GitHubService()
        assert hasattr(service, "get_portfolio_stats")
        assert callable(service.get_portfolio_stats)

    def test_get_project_stats_method_exists(self):
        """Test that get_project_stats method exists."""
        service = GitHubService()
        assert hasattr(service, "get_project_stats")
        assert callable(service.get_project_stats)


class TestGitHubServiceModuleLevel:
    """Tests for module level configuration."""

    def test_module_logger_exists(self):
        """Test that module logger is configured."""
        from app.services.github_service import logger  # noqa: PLC0415

        assert logger is not None

    def test_module_settings_import(self):
        """Test that settings is imported."""
        from app.services.github_service import settings  # noqa: PLC0415

        assert settings is not None

    def test_service_httpx_client_exists(self):
        """Test that AsyncClient is imported."""
        import httpx  # noqa: PLC0415

        assert httpx.AsyncClient is not None

    def test_service_base_url_constant(self):
        """Test base URL is HTTPS GitHub API."""
        service = GitHubService()
        assert service.base_url.startswith("https://")
        assert "github.com" in service.base_url


# Use separate event loops for async tests to avoid conftest conflicts
@pytest.fixture
def new_event_loop():
    """Create a fresh event loop for each async test."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestGetUserInfo:
    """Tests for get_user_info method."""

    def test_get_user_info_success(self, new_event_loop):
        """Test successful user info fetch."""

        async def run_test():
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "login": "testuser",
                "avatar_url": "https://example.com/avatar.png",
                "bio": "Test bio",
            }
            mock_response.raise_for_status = MagicMock()

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                service = GitHubService()
                result = await service.get_user_info("testuser")
                assert result["login"] == "testuser"

        new_event_loop.run_until_complete(run_test())

    def test_get_user_info_http_error(self, new_event_loop):
        """Test user info fetch with HTTP error returns empty dict."""

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    side_effect=httpx.HTTPError("Not found")
                )
                service = GitHubService()
                result = await service.get_user_info("nonexistent")
                assert result == {}

        new_event_loop.run_until_complete(run_test())


class TestGetUserRepos:
    """Tests for get_user_repos method."""

    def test_get_user_repos_http_error(self, new_event_loop):
        """Test repos fetch with HTTP error returns empty list."""

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    side_effect=httpx.HTTPError("Error")
                )
                service = GitHubService()
                result = await service.get_user_repos("testuser")
                assert result == []

        new_event_loop.run_until_complete(run_test())


class TestGetRepoDetails:
    """Tests for get_repo_details method."""

    def test_get_repo_details_success(self, new_event_loop):
        """Test successful repo details fetch."""

        async def run_test():
            mock_repo = {"name": "test-repo", "stargazers_count": 100}
            mock_response = MagicMock()
            mock_response.json.return_value = mock_repo
            mock_response.raise_for_status = MagicMock()

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                service = GitHubService()
                result = await service.get_repo_details("owner", "test-repo")
                assert result["name"] == "test-repo"

        new_event_loop.run_until_complete(run_test())

    def test_get_repo_details_http_error(self, new_event_loop):
        """Test repo details fetch with HTTP error returns empty dict."""

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    side_effect=httpx.HTTPError("Not found")
                )
                service = GitHubService()
                result = await service.get_repo_details("owner", "nonexistent")
                assert result == {}

        new_event_loop.run_until_complete(run_test())


class TestGetRepoLanguages:
    """Tests for get_repo_languages method."""

    def test_get_repo_languages_success(self, new_event_loop):
        """Test successful languages fetch."""

        async def run_test():
            mock_languages = {"Python": 50000, "JavaScript": 30000}
            mock_response = MagicMock()
            mock_response.json.return_value = mock_languages
            mock_response.raise_for_status = MagicMock()

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                service = GitHubService()
                result = await service.get_repo_languages("owner", "repo")
                assert result["Python"] == 50000

        new_event_loop.run_until_complete(run_test())

    def test_get_repo_languages_http_error(self, new_event_loop):
        """Test languages fetch with HTTP error returns empty dict."""

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    side_effect=httpx.HTTPError("Error")
                )
                service = GitHubService()
                result = await service.get_repo_languages("owner", "repo")
                assert result == {}

        new_event_loop.run_until_complete(run_test())


class TestGetRepoCommits:
    """Tests for get_repo_commits method."""

    def test_get_repo_commits_with_link_header(self, new_event_loop):
        """Test commit count extraction from Link header."""

        async def run_test():
            mock_response = MagicMock()
            mock_response.json.return_value = [{"sha": "abc123"}]
            mock_response.raise_for_status = MagicMock()
            mock_response.headers = {
                "Link": '<https://api.github.com/repos/o/r/commits?page=150>; rel="last"'
            }

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                service = GitHubService()
                result = await service.get_repo_commits("owner", "repo")
                assert result == 150

        new_event_loop.run_until_complete(run_test())

    def test_get_repo_commits_no_link_header(self, new_event_loop):
        """Test commit count without Link header."""

        async def run_test():
            mock_response = MagicMock()
            mock_response.json.return_value = [{"sha": "abc"}, {"sha": "def"}]
            mock_response.raise_for_status = MagicMock()
            mock_response.headers = {}

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                service = GitHubService()
                result = await service.get_repo_commits("owner", "repo")
                assert result == 2

        new_event_loop.run_until_complete(run_test())

    def test_get_repo_commits_http_error(self, new_event_loop):
        """Test commit count with HTTP error returns 0."""

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    side_effect=httpx.HTTPError("Error")
                )
                service = GitHubService()
                result = await service.get_repo_commits("owner", "repo")
                assert result == 0

        new_event_loop.run_until_complete(run_test())


class TestGetPortfolioStats:
    """Tests for get_portfolio_stats method."""

    def test_get_portfolio_stats_success(self, new_event_loop):
        """Test successful portfolio stats aggregation."""

        async def run_test():
            service = GitHubService()

            mock_user_info = {
                "avatar_url": "https://example.com/avatar.png",
                "bio": "Developer",
                "public_repos": 5,
                "followers": 100,
                "following": 50,
            }
            mock_repos = [
                {
                    "name": "repo1",
                    "stargazers_count": 10,
                    "forks_count": 5,
                    "watchers_count": 10,
                    "fork": False,
                },
                {
                    "name": "repo2",
                    "stargazers_count": 20,
                    "forks_count": 10,
                    "watchers_count": 20,
                    "fork": False,
                },
            ]
            mock_languages = {"Python": 10000}

            service.get_user_info = AsyncMock(return_value=mock_user_info)
            service.get_user_repos = AsyncMock(return_value=mock_repos)
            service.get_repo_languages = AsyncMock(return_value=mock_languages)

            result = await service.get_portfolio_stats("testuser")

            assert result["username"] == "testuser"
            assert result["total_stars"] == 30
            assert result["followers"] == 100

        new_event_loop.run_until_complete(run_test())

    def test_get_portfolio_stats_no_repos(self, new_event_loop):
        """Test portfolio stats with no repos."""

        async def run_test():
            service = GitHubService()

            service.get_user_info = AsyncMock(
                return_value={
                    "avatar_url": None,
                    "bio": None,
                    "public_repos": 0,
                    "followers": 0,
                    "following": 0,
                }
            )
            service.get_user_repos = AsyncMock(return_value=[])
            service.get_repo_languages = AsyncMock(return_value={})
            service.get_pinned_repos = AsyncMock(return_value=[])

            result = await service.get_portfolio_stats("newuser")

            assert result["total_stars"] == 0
            assert result["featured_repos"] == []

        new_event_loop.run_until_complete(run_test())


class TestGetProjectStats:
    """Tests for get_project_stats method."""

    def test_get_project_stats_success(self, new_event_loop):
        """Test successful project stats fetch."""

        async def run_test():
            service = GitHubService()

            mock_repo_details = {
                "name": "test-repo",
                "stargazers_count": 100,
                "forks_count": 50,
                "topics": ["python"],
            }

            service.get_repo_details = AsyncMock(return_value=mock_repo_details)
            service.get_repo_languages = AsyncMock(return_value={"Python": 50000})
            service.get_repo_commits = AsyncMock(return_value=250)

            result = await service.get_project_stats("owner", "test-repo")

            assert result["name"] == "test-repo"
            assert result["stars"] == 100
            assert result["commit_count"] == 250

        new_event_loop.run_until_complete(run_test())

    def test_get_project_stats_empty_repo(self, new_event_loop):
        """Test project stats for non-existent repo returns defaults."""

        async def run_test():
            service = GitHubService()

            service.get_repo_details = AsyncMock(return_value={})
            service.get_repo_languages = AsyncMock(return_value={})
            service.get_repo_commits = AsyncMock(return_value=0)

            result = await service.get_project_stats("owner", "nonexistent")

            assert result["name"] is None
            assert result["stars"] == 0

        new_event_loop.run_until_complete(run_test())
