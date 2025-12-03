"""
Tests for GitHub service module - initialization and configuration
"""

from unittest.mock import patch

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
        from app.services.github_service import logger

        assert logger is not None

    def test_module_settings_import(self):
        """Test that settings is imported."""
        from app.services.github_service import settings

        assert settings is not None

    def test_service_httpx_client_exists(self):
        """Test that AsyncClient is imported."""
        import httpx

        assert httpx.AsyncClient is not None

    def test_service_base_url_constant(self):
        """Test base URL is HTTPS GitHub API."""
        service = GitHubService()
        assert service.base_url.startswith("https://")
        assert "github.com" in service.base_url
