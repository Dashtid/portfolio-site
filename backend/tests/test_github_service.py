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
                mock_client.return_value.request = AsyncMock(return_value=mock_response)
                service = GitHubService()
                result = await service.get_user_info("testuser")
                assert result["login"] == "testuser"

        new_event_loop.run_until_complete(run_test())

    def test_get_user_info_http_error(self, new_event_loop):
        """Test user info fetch with HTTP error returns empty dict."""

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.request = AsyncMock(
                    side_effect=httpx.RequestError("Not found")
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
                mock_client.return_value.request = AsyncMock(
                    side_effect=httpx.RequestError("Error")
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
                mock_client.return_value.request = AsyncMock(return_value=mock_response)
                service = GitHubService()
                result = await service.get_repo_details("owner", "test-repo")
                assert result["name"] == "test-repo"

        new_event_loop.run_until_complete(run_test())

    def test_get_repo_details_http_error(self, new_event_loop):
        """Test repo details fetch with HTTP error returns empty dict."""

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.request = AsyncMock(
                    side_effect=httpx.RequestError("Not found")
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
                mock_client.return_value.request = AsyncMock(return_value=mock_response)
                service = GitHubService()
                result = await service.get_repo_languages("owner", "repo")
                assert result["Python"] == 50000

        new_event_loop.run_until_complete(run_test())

    def test_get_repo_languages_http_error(self, new_event_loop):
        """Test languages fetch with HTTP error returns empty dict."""

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.request = AsyncMock(
                    side_effect=httpx.RequestError("Error")
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
                mock_client.return_value.request = AsyncMock(return_value=mock_response)
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
                mock_client.return_value.request = AsyncMock(return_value=mock_response)
                service = GitHubService()
                result = await service.get_repo_commits("owner", "repo")
                assert result == 2

        new_event_loop.run_until_complete(run_test())

    def test_get_repo_commits_http_error(self, new_event_loop):
        """Test commit count with HTTP error returns 0."""

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.request = AsyncMock(
                    side_effect=httpx.RequestError("Error")
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


class TestClientConnectionPool:
    """Tests for AsyncClient connection pooling and lifecycle."""

    def test_get_client_creates_new_client(self, new_event_loop):
        """Test _get_client creates a new client when none exists."""

        async def run_test():
            service = GitHubService()
            assert service._client is None

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.is_closed = False
                mock_client_class.return_value = mock_client

                client = await service._get_client()
                assert client is mock_client
                mock_client_class.assert_called_once()

        new_event_loop.run_until_complete(run_test())

    def test_get_client_reuses_existing_client(self, new_event_loop):
        """Test _get_client reuses existing open client."""

        async def run_test():
            service = GitHubService()
            mock_client = MagicMock()
            mock_client.is_closed = False
            service._client = mock_client

            with patch("httpx.AsyncClient") as mock_client_class:
                client = await service._get_client()
                assert client is mock_client
                mock_client_class.assert_not_called()

        new_event_loop.run_until_complete(run_test())

    def test_get_client_recreates_closed_client(self, new_event_loop):
        """Test _get_client creates new client when existing is closed."""

        async def run_test():
            service = GitHubService()
            old_client = MagicMock()
            old_client.is_closed = True
            service._client = old_client

            with patch("httpx.AsyncClient") as mock_client_class:
                new_client = MagicMock()
                new_client.is_closed = False
                mock_client_class.return_value = new_client

                client = await service._get_client()
                assert client is new_client
                mock_client_class.assert_called_once()

        new_event_loop.run_until_complete(run_test())

    def test_close_closes_open_client(self, new_event_loop):
        """Test close() properly closes an open client."""

        async def run_test():
            service = GitHubService()
            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.aclose = AsyncMock()
            service._client = mock_client

            await service.close()

            mock_client.aclose.assert_called_once()
            assert service._client is None

        new_event_loop.run_until_complete(run_test())

    def test_close_does_nothing_when_no_client(self, new_event_loop):
        """Test close() handles missing client gracefully."""

        async def run_test():
            service = GitHubService()
            assert service._client is None
            await service.close()  # Should not raise
            assert service._client is None

        new_event_loop.run_until_complete(run_test())

    def test_close_does_nothing_when_client_already_closed(self, new_event_loop):
        """Test close() handles already closed client."""

        async def run_test():
            service = GitHubService()
            mock_client = MagicMock()
            mock_client.is_closed = True
            service._client = mock_client

            await service.close()  # Should not call aclose
            # Client should remain unchanged since is_closed was True

        new_event_loop.run_until_complete(run_test())


class TestRateLimitRetry:
    """Tests for rate limit (429) handling with backoff."""

    def test_rate_limit_429_with_retry_after_header(self, new_event_loop):
        """Test 429 response with Retry-After header triggers retry."""

        async def run_test():
            service = GitHubService()

            # First call returns 429, second call succeeds
            rate_limit_response = MagicMock()
            rate_limit_response.status_code = 429
            rate_limit_response.headers = {"Retry-After": "0.01"}  # 10ms

            success_response = MagicMock()
            success_response.status_code = 200
            success_response.json.return_value = {"login": "testuser"}
            success_response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(side_effect=[rate_limit_response, success_response])

            with (
                patch("httpx.AsyncClient", return_value=mock_client),
                patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
            ):
                result = await service.get_user_info("testuser")

                assert result["login"] == "testuser"
                mock_sleep.assert_called_once()
                # Should have parsed Retry-After header
                assert mock_sleep.call_args[0][0] == 0.01

        new_event_loop.run_until_complete(run_test())

    def test_rate_limit_429_invalid_retry_after_uses_backoff(self, new_event_loop):
        """Test 429 with invalid Retry-After uses exponential backoff."""

        async def run_test():
            service = GitHubService()

            rate_limit_response = MagicMock()
            rate_limit_response.status_code = 429
            rate_limit_response.headers = {"Retry-After": "invalid-date"}

            success_response = MagicMock()
            success_response.status_code = 200
            success_response.json.return_value = {"login": "testuser"}
            success_response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(side_effect=[rate_limit_response, success_response])

            with (
                patch("httpx.AsyncClient", return_value=mock_client),
                patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
            ):
                result = await service.get_user_info("testuser")

                assert result["login"] == "testuser"
                # Should use BASE_BACKOFF_SECONDS * (2**0) = 1.0
                assert mock_sleep.call_args[0][0] == 1.0

        new_event_loop.run_until_complete(run_test())

    def test_rate_limit_429_no_retry_after_uses_backoff(self, new_event_loop):
        """Test 429 without Retry-After header uses exponential backoff."""

        async def run_test():
            service = GitHubService()

            rate_limit_response = MagicMock()
            rate_limit_response.status_code = 429
            rate_limit_response.headers = {}  # No Retry-After

            success_response = MagicMock()
            success_response.status_code = 200
            success_response.json.return_value = {"login": "testuser"}
            success_response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(side_effect=[rate_limit_response, success_response])

            with (
                patch("httpx.AsyncClient", return_value=mock_client),
                patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
            ):
                result = await service.get_user_info("testuser")

                assert result["login"] == "testuser"
                # Should use BASE_BACKOFF_SECONDS * (2**0) = 1.0
                assert mock_sleep.call_args[0][0] == 1.0

        new_event_loop.run_until_complete(run_test())

    def test_rate_limit_max_retries_exceeded(self, new_event_loop):
        """Test returns None after MAX_RETRIES rate limit responses."""

        async def run_test():
            service = GitHubService()

            rate_limit_response = MagicMock()
            rate_limit_response.status_code = 429
            rate_limit_response.headers = {"Retry-After": "0.01"}

            mock_client = MagicMock()
            mock_client.is_closed = False
            # Return 429 for all 3 retries
            mock_client.request = AsyncMock(return_value=rate_limit_response)

            with (
                patch("httpx.AsyncClient", return_value=mock_client),
                patch("asyncio.sleep", new_callable=AsyncMock),
            ):
                result = await service.get_user_info("testuser")

                # Should return empty dict (None from _request_with_backoff)
                assert result == {}
                # Should have tried MAX_RETRIES times
                assert mock_client.request.call_count == 3

        new_event_loop.run_until_complete(run_test())


class TestTimeoutBackoff:
    """Tests for timeout handling with exponential backoff."""

    def test_timeout_triggers_retry(self, new_event_loop):
        """Test timeout triggers exponential backoff retry."""

        async def run_test():
            service = GitHubService()

            success_response = MagicMock()
            success_response.status_code = 200
            success_response.json.return_value = {"login": "testuser"}
            success_response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(
                side_effect=[httpx.TimeoutException("Timeout"), success_response]
            )

            with (
                patch("httpx.AsyncClient", return_value=mock_client),
                patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
            ):
                result = await service.get_user_info("testuser")

                assert result["login"] == "testuser"
                mock_sleep.assert_called_once()
                # Should use BASE_BACKOFF_SECONDS * (2**0) = 1.0
                assert mock_sleep.call_args[0][0] == 1.0

        new_event_loop.run_until_complete(run_test())

    def test_timeout_max_retries_returns_empty(self, new_event_loop):
        """Test returns empty dict after timeout retries exhausted."""

        async def run_test():
            service = GitHubService()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

            with (
                patch("httpx.AsyncClient", return_value=mock_client),
                patch("asyncio.sleep", new_callable=AsyncMock),
            ):
                result = await service.get_user_info("testuser")

                assert result == {}
                # Should have tried MAX_RETRIES times
                assert mock_client.request.call_count == 3

        new_event_loop.run_until_complete(run_test())

    def test_timeout_exponential_backoff_calculation(self, new_event_loop):
        """Test exponential backoff doubles each retry."""

        async def run_test():
            service = GitHubService()

            success_response = MagicMock()
            success_response.status_code = 200
            success_response.json.return_value = {"login": "testuser"}
            success_response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(
                side_effect=[
                    httpx.TimeoutException("Timeout"),
                    httpx.TimeoutException("Timeout"),
                    success_response,
                ]
            )

            with (
                patch("httpx.AsyncClient", return_value=mock_client),
                patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
            ):
                result = await service.get_user_info("testuser")

                assert result["login"] == "testuser"
                # Check exponential backoff: 1.0, 2.0
                assert mock_sleep.call_count == 2
                assert mock_sleep.call_args_list[0][0][0] == 1.0
                assert mock_sleep.call_args_list[1][0][0] == 2.0

        new_event_loop.run_until_complete(run_test())


class TestHTTPStatusErrors:
    """Tests for HTTPStatusError handling in various methods."""

    def test_get_user_info_http_status_error(self, new_event_loop):
        """Test get_user_info handles HTTPStatusError gracefully."""

        async def run_test():
            service = GitHubService()

            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not found", request=MagicMock(), response=mock_response
            )

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(return_value=mock_response)

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_user_info("nonexistent")
                assert result == {}

        new_event_loop.run_until_complete(run_test())

    def test_get_repo_details_http_status_error(self, new_event_loop):
        """Test get_repo_details handles HTTPStatusError gracefully."""

        async def run_test():
            service = GitHubService()

            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not found", request=MagicMock(), response=mock_response
            )

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(return_value=mock_response)

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_repo_details("owner", "nonexistent")
                assert result == {}

        new_event_loop.run_until_complete(run_test())

    def test_get_repo_languages_http_status_error(self, new_event_loop):
        """Test get_repo_languages handles HTTPStatusError gracefully."""

        async def run_test():
            service = GitHubService()

            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not found", request=MagicMock(), response=mock_response
            )

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(return_value=mock_response)

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_repo_languages("owner", "nonexistent")
                assert result == {}

        new_event_loop.run_until_complete(run_test())

    def test_get_repo_commits_http_status_error(self, new_event_loop):
        """Test get_repo_commits handles HTTPStatusError gracefully."""

        async def run_test():
            service = GitHubService()

            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not found", request=MagicMock(), response=mock_response
            )

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(return_value=mock_response)

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_repo_commits("owner", "nonexistent")
                assert result == 0

        new_event_loop.run_until_complete(run_test())


class TestPaginationEdgeCases:
    """Tests for get_user_repos pagination logic."""

    def test_pagination_respects_max_repos_limit(self, new_event_loop):
        """Test pagination stops when max_repos is reached."""

        async def run_test():
            service = GitHubService()

            # Return 10 repos per page
            page1_repos = [{"name": f"repo{i}"} for i in range(10)]
            page2_repos = [{"name": f"repo{i}"} for i in range(10, 20)]

            page1_response = MagicMock()
            page1_response.status_code = 200
            page1_response.json.return_value = page1_repos
            page1_response.raise_for_status = MagicMock()

            page2_response = MagicMock()
            page2_response.status_code = 200
            page2_response.json.return_value = page2_repos
            page2_response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(side_effect=[page1_response, page2_response])

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_user_repos("testuser", per_page=10, max_repos=15)

                # Should only return 15 repos (max_repos limit)
                assert len(result) == 15

        new_event_loop.run_until_complete(run_test())

    def test_pagination_stops_on_empty_page(self, new_event_loop):
        """Test pagination stops when an empty page is received."""

        async def run_test():
            service = GitHubService()

            # Use per_page=2 so we get a full page and need to check for more
            page1_repos = [{"name": "repo1"}, {"name": "repo2"}]

            page1_response = MagicMock()
            page1_response.status_code = 200
            page1_response.json.return_value = page1_repos
            page1_response.raise_for_status = MagicMock()

            empty_response = MagicMock()
            empty_response.status_code = 200
            empty_response.json.return_value = []
            empty_response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(side_effect=[page1_response, empty_response])

            with patch("httpx.AsyncClient", return_value=mock_client):
                # per_page=2 means first page is full, so pagination continues
                result = await service.get_user_repos("testuser", per_page=2, max_repos=100)

                assert len(result) == 2
                # Should have made 2 requests (first full page + empty second page)
                assert mock_client.request.call_count == 2

        new_event_loop.run_until_complete(run_test())

    def test_pagination_stops_on_partial_page(self, new_event_loop):
        """Test pagination stops when page has fewer items than per_page."""

        async def run_test():
            service = GitHubService()

            # Only 5 repos returned when per_page is 10
            partial_repos = [{"name": f"repo{i}"} for i in range(5)]

            response = MagicMock()
            response.status_code = 200
            response.json.return_value = partial_repos
            response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(return_value=response)

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_user_repos("testuser", per_page=10, max_repos=100)

                assert len(result) == 5
                # Should only make one request
                assert mock_client.request.call_count == 1

        new_event_loop.run_until_complete(run_test())

    def test_pagination_http_error_mid_pagination(self, new_event_loop):
        """Test pagination handles HTTP error during pagination."""

        async def run_test():
            service = GitHubService()

            page1_repos = [{"name": f"repo{i}"} for i in range(10)]

            page1_response = MagicMock()
            page1_response.status_code = 200
            page1_response.json.return_value = page1_repos
            page1_response.raise_for_status = MagicMock()

            error_response = MagicMock()
            error_response.status_code = 500
            error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server error", request=MagicMock(), response=error_response
            )

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(side_effect=[page1_response, error_response])

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_user_repos("testuser", per_page=10, max_repos=100)

                # Should return first page of repos
                assert len(result) == 10

        new_event_loop.run_until_complete(run_test())


class TestGraphQLErrorHandling:
    """Tests for get_pinned_repos GraphQL error handling."""

    def test_graphql_errors_in_response(self, new_event_loop):
        """Test handling of GraphQL errors array in response."""

        async def run_test():
            service = GitHubService()

            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {
                "errors": [{"message": "User not found"}],
                "data": None,
            }
            response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(return_value=response)

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_pinned_repos("nonexistent")
                assert result == []

        new_event_loop.run_until_complete(run_test())

    def test_graphql_null_user(self, new_event_loop):
        """Test handling of null user in GraphQL response."""

        async def run_test():
            service = GitHubService()

            response = MagicMock()
            response.status_code = 200
            # When user doesn't exist, GitHub returns empty data, not null user
            response.json.return_value = {"data": {}}
            response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(return_value=response)

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_pinned_repos("nonexistent")
                assert result == []

        new_event_loop.run_until_complete(run_test())

    def test_graphql_null_pinned_items(self, new_event_loop):
        """Test handling of empty pinnedItems in response."""

        async def run_test():
            service = GitHubService()

            response = MagicMock()
            response.status_code = 200
            # When user has no pinned items, GitHub returns empty nodes array
            response.json.return_value = {"data": {"user": {"pinnedItems": {"nodes": []}}}}
            response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(return_value=response)

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_pinned_repos("testuser")
                assert result == []

        new_event_loop.run_until_complete(run_test())

    def test_graphql_null_nodes_in_list(self, new_event_loop):
        """Test filtering of null nodes in pinned items list."""

        async def run_test():
            service = GitHubService()

            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {
                "data": {
                    "user": {
                        "pinnedItems": {
                            "nodes": [
                                {
                                    "name": "repo1",
                                    "description": "Test repo",
                                    "url": "https://github.com/user/repo1",
                                    "stargazerCount": 10,
                                    "forkCount": 5,
                                    "primaryLanguage": {"name": "Python"},
                                },
                                None,  # Null node to filter out
                                {
                                    "name": "repo2",
                                    "description": None,
                                    "url": "https://github.com/user/repo2",
                                    "stargazerCount": 0,
                                    "forkCount": 0,
                                    "primaryLanguage": None,
                                },
                            ]
                        }
                    }
                }
            }
            response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(return_value=response)

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_pinned_repos("testuser")

                assert len(result) == 2
                assert result[0]["name"] == "repo1"
                assert result[0]["language"] == "Python"
                assert result[1]["name"] == "repo2"
                assert result[1]["language"] is None

        new_event_loop.run_until_complete(run_test())

    def test_graphql_http_status_error(self, new_event_loop):
        """Test get_pinned_repos handles HTTPStatusError gracefully."""

        async def run_test():
            service = GitHubService()

            response = MagicMock()
            response.status_code = 401
            response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Unauthorized", request=MagicMock(), response=response
            )

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(return_value=response)

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_pinned_repos("testuser")
                assert result == []

        new_event_loop.run_until_complete(run_test())


class TestLanguageAggregationExceptions:
    """Tests for exception handling in language aggregation (asyncio.gather)."""

    def test_language_aggregation_handles_exceptions(self, new_event_loop):
        """Test that language aggregation continues despite individual failures."""

        async def run_test():
            service = GitHubService()

            mock_user_info = {
                "avatar_url": "https://example.com/avatar.png",
                "bio": "Developer",
                "public_repos": 3,
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
                {
                    "name": "repo3",
                    "stargazers_count": 5,
                    "forks_count": 2,
                    "watchers_count": 5,
                    "fork": False,
                },
            ]

            service.get_user_info = AsyncMock(return_value=mock_user_info)
            service.get_user_repos = AsyncMock(return_value=mock_repos)
            service.get_pinned_repos = AsyncMock(return_value=[])

            # Mock get_repo_languages to return exception for one repo
            async def mock_get_languages(username: str, repo_name: str):
                if repo_name == "repo2":
                    raise httpx.RequestError("Network error")
                return {"Python": 10000} if repo_name == "repo1" else {"JavaScript": 5000}

            service.get_repo_languages = mock_get_languages

            result = await service.get_portfolio_stats("testuser")

            # Should still have language stats from successful calls
            assert result["username"] == "testuser"
            assert len(result["top_languages"]) > 0
            # Total should only include successful fetches
            total_percentage = sum(lang["percentage"] for lang in result["top_languages"])
            assert total_percentage == 100.0

        new_event_loop.run_until_complete(run_test())

    def test_language_aggregation_all_failures(self, new_event_loop):
        """Test that language aggregation handles all failures gracefully."""

        async def run_test():
            service = GitHubService()

            mock_user_info = {
                "avatar_url": None,
                "bio": None,
                "public_repos": 1,
                "followers": 0,
                "following": 0,
            }
            mock_repos = [
                {
                    "name": "repo1",
                    "stargazers_count": 0,
                    "forks_count": 0,
                    "watchers_count": 0,
                    "fork": False,
                },
            ]

            service.get_user_info = AsyncMock(return_value=mock_user_info)
            service.get_user_repos = AsyncMock(return_value=mock_repos)
            service.get_pinned_repos = AsyncMock(return_value=[])

            # All language fetches fail
            async def mock_get_languages(username: str, repo_name: str):
                raise httpx.RequestError("Network error")

            service.get_repo_languages = mock_get_languages

            result = await service.get_portfolio_stats("testuser")

            # Should return empty languages
            assert result["top_languages"] == []

        new_event_loop.run_until_complete(run_test())
