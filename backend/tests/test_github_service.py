"""
Tests for GitHub service module - initialization, configuration, and API methods
"""

import asyncio
import time
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

    def test_get_repo_languages_method_exists(self):
        """Test that get_repo_languages method exists."""
        service = GitHubService()
        assert hasattr(service, "get_repo_languages")
        assert callable(service.get_repo_languages)

    def test_get_portfolio_stats_method_exists(self):
        """Test that get_portfolio_stats method exists."""
        service = GitHubService()
        assert hasattr(service, "get_portfolio_stats")
        assert callable(service.get_portfolio_stats)


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


class TestRequestWithBackoffRequestError:
    """Tests for _request_with_backoff handling generic RequestError."""

    def test_request_error_returns_none(self, new_event_loop):
        """Test generic RequestError returns None immediately (no retry)."""

        async def run_test():
            service = GitHubService()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(side_effect=httpx.RequestError("Connection refused"))

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service._request_with_backoff("GET", "https://test.com")

                assert result is None
                # Should only try once for generic RequestError (no retry)
                assert mock_client.request.call_count == 1

        new_event_loop.run_until_complete(run_test())

    def test_request_error_in_get_user_info(self, new_event_loop):
        """Test generic RequestError in get_user_info returns empty dict."""

        async def run_test():
            service = GitHubService()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(side_effect=httpx.RequestError("DNS resolution failed"))

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_user_info("testuser")
                assert result == {}

        new_event_loop.run_until_complete(run_test())

    def test_request_error_in_get_user_repos(self, new_event_loop):
        """Test generic RequestError in get_user_repos returns empty list."""

        async def run_test():
            service = GitHubService()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(side_effect=httpx.RequestError("Connection reset"))

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_user_repos("testuser")
                assert result == []

        new_event_loop.run_until_complete(run_test())


class TestUserReposPaginationBoundaries:
    """Tests for get_user_repos pagination boundary conditions."""

    def test_per_page_adjusted_near_max_repos(self, new_event_loop):
        """Test per_page is adjusted when near max_repos limit."""

        async def run_test():
            service = GitHubService()

            # Return 8 repos (max_repos=10, so next request should only ask for 2)
            page1_repos = [{"name": f"repo{i}"} for i in range(8)]
            page2_repos = [{"name": "repo8"}, {"name": "repo9"}]

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
                result = await service.get_user_repos("testuser", per_page=8, max_repos=10)

                assert len(result) == 10
                # Verify the second request asked for only 2 repos
                second_call_params = mock_client.request.call_args_list[1][1]["params"]
                assert second_call_params["per_page"] == 2

        new_event_loop.run_until_complete(run_test())

    def test_exact_max_repos_on_first_page(self, new_event_loop):
        """Test when first page returns exactly max_repos items."""

        async def run_test():
            service = GitHubService()

            repos = [{"name": f"repo{i}"} for i in range(5)]

            response = MagicMock()
            response.status_code = 200
            response.json.return_value = repos
            response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(return_value=response)

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_user_repos("testuser", per_page=10, max_repos=5)

                assert len(result) == 5
                # Only one request needed
                assert mock_client.request.call_count == 1

        new_event_loop.run_until_complete(run_test())

    def test_user_has_no_repos(self, new_event_loop):
        """Test handling user with no repositories."""

        async def run_test():
            service = GitHubService()

            response = MagicMock()
            response.status_code = 200
            response.json.return_value = []
            response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(return_value=response)

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_user_repos("newuser")

                assert result == []
                assert mock_client.request.call_count == 1

        new_event_loop.run_until_complete(run_test())


class TestPortfolioStatsForkFiltering:
    """Tests for fork filtering in get_portfolio_stats."""

    def test_forks_excluded_from_stats(self, new_event_loop):
        """Test that forked repos are excluded from statistics."""

        async def run_test():
            service = GitHubService()

            mock_user_info = {
                "avatar_url": "https://example.com/avatar.png",
                "bio": "Developer",
                "public_repos": 4,
                "followers": 50,
                "following": 25,
            }
            mock_repos = [
                {
                    "name": "my-repo",
                    "stargazers_count": 100,
                    "forks_count": 10,
                    "watchers_count": 100,
                    "fork": False,
                },
                {
                    "name": "forked-repo",
                    "stargazers_count": 500,
                    "forks_count": 100,
                    "watchers_count": 500,
                    "fork": True,
                },  # This should be excluded
                {
                    "name": "another-repo",
                    "stargazers_count": 50,
                    "forks_count": 5,
                    "watchers_count": 50,
                    "fork": False,
                },
            ]

            service.get_user_info = AsyncMock(return_value=mock_user_info)
            service.get_user_repos = AsyncMock(return_value=mock_repos)
            service.get_repo_languages = AsyncMock(return_value={"Python": 1000})
            service.get_pinned_repos = AsyncMock(return_value=[])

            result = await service.get_portfolio_stats("testuser")

            # Only owned repos should count: 100 + 50 = 150
            assert result["total_stars"] == 150
            # Forked repo's 500 stars should not be included
            assert result["total_forks"] == 15  # 10 + 5, not 110

        new_event_loop.run_until_complete(run_test())

    def test_all_repos_are_forks(self, new_event_loop):
        """Test handling when all repos are forks."""

        async def run_test():
            service = GitHubService()

            mock_user_info = {
                "avatar_url": None,
                "bio": None,
                "public_repos": 2,
                "followers": 0,
                "following": 0,
            }
            mock_repos = [
                {
                    "name": "fork1",
                    "stargazers_count": 10,
                    "forks_count": 1,
                    "watchers_count": 10,
                    "fork": True,
                },
                {
                    "name": "fork2",
                    "stargazers_count": 20,
                    "forks_count": 2,
                    "watchers_count": 20,
                    "fork": True,
                },
            ]

            service.get_user_info = AsyncMock(return_value=mock_user_info)
            service.get_user_repos = AsyncMock(return_value=mock_repos)
            service.get_repo_languages = AsyncMock(return_value={})
            service.get_pinned_repos = AsyncMock(return_value=[])

            result = await service.get_portfolio_stats("testuser")

            assert result["total_stars"] == 0
            assert result["total_forks"] == 0
            assert result["featured_repos"] == []

        new_event_loop.run_until_complete(run_test())


class TestPortfolioStatsDivisionByZero:
    """Tests for division by zero handling in language percentage calculation."""

    def test_zero_total_bytes_returns_zero_percentage(self, new_event_loop):
        """Test language percentage is 0 when total_bytes is 0."""

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
                    "name": "empty-repo",
                    "stargazers_count": 0,
                    "forks_count": 0,
                    "watchers_count": 0,
                    "fork": False,
                },
            ]

            service.get_user_info = AsyncMock(return_value=mock_user_info)
            service.get_user_repos = AsyncMock(return_value=mock_repos)
            # Return empty languages (no code)
            service.get_repo_languages = AsyncMock(return_value={})
            service.get_pinned_repos = AsyncMock(return_value=[])

            result = await service.get_portfolio_stats("testuser")

            # Should not crash, should return empty languages
            assert result["top_languages"] == []

        new_event_loop.run_until_complete(run_test())


class TestPinnedReposEdgeCases:
    """Additional tests for get_pinned_repos edge cases."""

    def test_pinned_repos_with_missing_data_key(self, new_event_loop):
        """Test handling of missing data key in GraphQL response."""

        async def run_test():
            service = GitHubService()

            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {}  # Missing "data" key
            response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(return_value=response)

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_pinned_repos("nonexistent")
                assert result == []

        new_event_loop.run_until_complete(run_test())

    def test_pinned_repos_missing_pinned_items(self, new_event_loop):
        """Test handling when pinnedItems is missing from user."""

        async def run_test():
            service = GitHubService()

            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {"data": {"user": {}}}
            response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(return_value=response)

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_pinned_repos("testuser")
                assert result == []

        new_event_loop.run_until_complete(run_test())

    def test_pinned_repos_request_error(self, new_event_loop):
        """Test get_pinned_repos handles RequestError gracefully."""

        async def run_test():
            service = GitHubService()

            mock_client = MagicMock()
            mock_client.is_closed = False
            mock_client.request = AsyncMock(side_effect=httpx.RequestError("Connection failed"))

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await service.get_pinned_repos("testuser")
                assert result == []

        new_event_loop.run_until_complete(run_test())

    def test_pinned_repos_success_full_data(self, new_event_loop):
        """Test successful fetch with complete data."""

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
                                    "name": "awesome-project",
                                    "description": "An awesome project",
                                    "url": "https://github.com/user/awesome-project",
                                    "stargazerCount": 100,
                                    "forkCount": 25,
                                    "primaryLanguage": {"name": "TypeScript"},
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

                assert len(result) == 1
                assert result[0]["name"] == "awesome-project"
                assert result[0]["stars"] == 100
                assert result[0]["language"] == "TypeScript"

        new_event_loop.run_until_complete(run_test())


class TestPortfolioStatsCacheResilience:
    """Deadline, failure-TTL, stale-serving and bounding of the stats cache."""

    @staticmethod
    def _failing_helpers(service: GitHubService) -> None:
        """Simulate every upstream stage failing (helpers swallow errors)."""
        service.get_user_info = AsyncMock(return_value={})  # type: ignore[method-assign]
        service.get_user_repos = AsyncMock(return_value=[])  # type: ignore[method-assign]
        service.get_repo_languages = AsyncMock(return_value={})  # type: ignore[method-assign]
        service.get_pinned_repos = AsyncMock(return_value=[])  # type: ignore[method-assign]

    def test_failure_cached_only_briefly(self, new_event_loop):
        """All-stages-failed zeros must use the short failure TTL, not 5 min."""
        from app.services.github_service import (  # noqa: PLC0415
            GITHUB_STATS_CACHE_TTL_SECONDS,
            GITHUB_STATS_FAILURE_TTL_SECONDS,
        )

        async def run_test():
            service = GitHubService()
            self._failing_helpers(service)

            result = await service.get_portfolio_stats("ghost")

            assert result["total_stars"] == 0
            value, expires_at, ok = service._stats_cache["ghost"]
            assert ok is False
            remaining = expires_at - time.monotonic()
            assert remaining <= GITHUB_STATS_FAILURE_TTL_SECONDS + 1
            assert remaining < GITHUB_STATS_CACHE_TTL_SECONDS

        new_event_loop.run_until_complete(run_test())

    def test_stale_good_value_served_on_failed_refresh(self, new_event_loop):
        """An expired good entry beats fresh zeros when GitHub is down."""

        async def run_test():
            service = GitHubService()
            good = {"username": "dashtid", "avatar_url": "https://a.png", "total_stars": 42}
            service._stats_cache["dashtid"] = (good, time.monotonic() - 1, True)
            self._failing_helpers(service)

            result = await service.get_portfolio_stats("dashtid")

            assert result is good
            value, _expires, ok = service._stats_cache["dashtid"]
            assert value is good
            assert ok is True

        new_event_loop.run_until_complete(run_test())

    def test_deadline_produces_failure_entry(self, new_event_loop, monkeypatch):
        """A fan-out exceeding the overall deadline returns zeroed stats."""
        import sys  # noqa: PLC0415

        # NB: `import app.services.github_service as m` would bind the
        # singleton INSTANCE (app/services/__init__.py re-exports a name
        # that shadows the submodule); go through sys.modules instead.
        gs_module = sys.modules["app.services.github_service"]
        monkeypatch.setattr(gs_module, "PORTFOLIO_STATS_DEADLINE_SECONDS", 0.05)

        async def run_test():
            service = GitHubService()

            async def hang(username: str) -> tuple[dict, bool]:
                await asyncio.sleep(5)
                return {}, False

            service._fetch_portfolio_stats = hang  # type: ignore[method-assign]

            result = await service.get_portfolio_stats("slowpoke")

            assert result["username"] == "slowpoke"
            assert result["total_stars"] == 0
            _value, _expires, ok = service._stats_cache["slowpoke"]
            assert ok is False

        new_event_loop.run_until_complete(run_test())

    def test_cache_and_locks_are_bounded(self):
        """The public endpoint takes any username; dicts must not grow unbounded."""
        from app.services.github_service import STATS_CACHE_MAX_ENTRIES  # noqa: PLC0415

        service = GitHubService()
        for i in range(STATS_CACHE_MAX_ENTRIES * 3):
            username = f"user-{i}"
            service._stats_locks.setdefault(username, asyncio.Lock())
            service._store(username, {"username": username}, ttl=300, ok=True)

        assert len(service._stats_cache) == STATS_CACHE_MAX_ENTRIES
        assert len(service._stats_locks) <= STATS_CACHE_MAX_ENTRIES + 1
        # Most recent insertions survive (LRU evicts the oldest untouched).
        assert f"user-{STATS_CACHE_MAX_ENTRIES * 3 - 1}" in service._stats_cache

    def test_lru_eviction_spares_touched_entries_and_never_self_evicts(self):
        """Visitor-touched entries (the portfolio owner) survive attacker churn.

        Also: a just-stored entry must never be its own eviction victim,
        even when it has the earliest expiry in the cache (30s failure TTL
        vs everyone else's 300s).
        """
        from app.services.github_service import STATS_CACHE_MAX_ENTRIES  # noqa: PLC0415

        service = GitHubService()
        service._store("dashtid", {"username": "dashtid"}, ttl=300, ok=True)
        for i in range(STATS_CACHE_MAX_ENTRIES - 1):
            service._store(f"filler-{i}", {"username": f"filler-{i}"}, ttl=300, ok=True)

        # A visitor hits the owner's entry -> LRU bump.
        service._touch("dashtid")

        # Attacker churns garbage names stored at the SHORT failure TTL.
        for i in range(10):
            service._store(f"garbage-{i}", {"username": f"garbage-{i}"}, ttl=30, ok=False)
            # The just-stored garbage entry is present (not self-evicted)...
            assert f"garbage-{i}" in service._stats_cache

        # ...and the touched owner entry survived all the churn.
        assert "dashtid" in service._stats_cache
        assert len(service._stats_cache) == STATS_CACHE_MAX_ENTRIES

    def test_idle_locks_swept_when_username_leaves_cache(self):
        """Orphaned locks are reclaimed; held/awaited locks are not."""
        service = GitHubService()
        idle = asyncio.Lock()
        service._stats_locks["gone-idle"] = idle

        held = asyncio.Lock()
        held._locked = True  # simulate a coroutine mid-fetch
        service._stats_locks["gone-held"] = held

        service._store("someone", {"username": "someone"}, ttl=300, ok=True)

        assert "gone-idle" not in service._stats_locks
        assert "gone-held" in service._stats_locks

    def test_partial_failure_uses_short_ttl(self, new_event_loop):
        """user_info ok but repos stage failed -> not cached at full TTL."""
        from app.services.github_service import GITHUB_STATS_CACHE_TTL_SECONDS  # noqa: PLC0415

        async def run_test():
            service = GitHubService()
            service.get_user_info = AsyncMock(  # type: ignore[method-assign]
                return_value={"avatar_url": "https://a.png", "public_repos": 12}
            )
            # Repos stage fails (rate-limited REST) while GraphQL succeeds.
            service.get_user_repos = AsyncMock(return_value=[])  # type: ignore[method-assign]
            service.get_repo_languages = AsyncMock(return_value={})  # type: ignore[method-assign]
            service.get_pinned_repos = AsyncMock(  # type: ignore[method-assign]
                return_value=[{"name": "pinned-repo", "stars": 5}]
            )

            result = await service.get_portfolio_stats("dashtid")

            # Partial data is served, but flagged failed -> short TTL.
            assert result["public_repos"] == 12
            _value, expires_at, ok = service._stats_cache["dashtid"]
            assert ok is False
            assert expires_at - time.monotonic() < GITHUB_STATS_CACHE_TTL_SECONDS

        new_event_loop.run_until_complete(run_test())

    def test_gather_stage_exception_treated_as_failure(self, new_event_loop):
        """A helper raising (malformed 200 body) must not 500 the endpoint."""

        async def run_test():
            service = GitHubService()
            service.get_user_info = AsyncMock(  # type: ignore[method-assign]
                side_effect=ValueError("malformed JSON body")
            )
            service.get_user_repos = AsyncMock(return_value=[])  # type: ignore[method-assign]
            service.get_repo_languages = AsyncMock(return_value={})  # type: ignore[method-assign]
            service.get_pinned_repos = AsyncMock(return_value=[])  # type: ignore[method-assign]

            result = await service.get_portfolio_stats("brokenjson")

            assert result["total_stars"] == 0
            _value, _expires, ok = service._stats_cache["brokenjson"]
            assert ok is False

        new_event_loop.run_until_complete(run_test())
