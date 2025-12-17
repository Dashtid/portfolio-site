"""
Tests for configuration module
"""

from app.config import Settings


class TestSettings:
    """Tests for Settings configuration class."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()

        # Check some defaults based on actual config
        assert settings.APP_NAME == "Portfolio API"
        assert settings.APP_VERSION == "0.1.0"
        assert settings.ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0

    def test_cors_origins_default(self):
        """Test CORS origins default."""
        settings = Settings()

        # Should be a list (either default or parsed from env)
        assert isinstance(settings.CORS_ORIGINS, list)

    def test_database_url_default(self):
        """Test database URL has a default."""
        settings = Settings()

        assert settings.DATABASE_URL is not None
        assert len(settings.DATABASE_URL) > 0

    def test_log_level_default(self):
        """Test log level default."""
        settings = Settings()

        assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_debug_default(self):
        """Test debug mode default."""
        settings = Settings()

        # Debug should be a boolean
        assert isinstance(settings.DEBUG, bool)

    def test_error_tracking_settings(self):
        """Test error tracking settings."""
        settings = Settings()

        assert isinstance(settings.ERROR_TRACKING_ENABLED, bool)

    def test_metrics_enabled_settings(self):
        """Test metrics monitoring settings."""
        settings = Settings()

        assert isinstance(settings.METRICS_ENABLED, bool)

    def test_analytics_settings(self):
        """Test analytics settings."""
        settings = Settings()

        assert isinstance(settings.ANALYTICS_ENABLED, bool)

    def test_async_database_url_property(self):
        """Test async_database_url property converts URL correctly."""
        settings = Settings()

        # Should return a string
        async_url = settings.async_database_url
        assert isinstance(async_url, str)

    def test_server_settings(self):
        """Test server configuration defaults."""
        settings = Settings()

        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000

    def test_secret_key_exists(self):
        """Test that secret key is generated."""
        settings = Settings()

        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 0

    def test_environment_setting(self):
        """Test environment setting."""
        settings = Settings()

        assert settings.ENVIRONMENT in ["development", "production", "testing"]


class TestAsyncDatabaseUrl:
    """Tests for async_database_url property."""

    def test_async_url_with_postgres_prefix(self):
        """Test conversion of postgres:// to postgresql+asyncpg://."""
        settings = Settings()
        settings.DATABASE_URL = "postgres://user:pass@host:5432/db"
        async_url = settings.async_database_url
        assert async_url.startswith("postgresql+asyncpg://")
        assert "user:pass@host:5432/db" in async_url

    def test_async_url_with_postgresql_prefix(self):
        """Test conversion of postgresql:// to postgresql+asyncpg://."""
        settings = Settings()
        settings.DATABASE_URL = "postgresql://user:pass@host:5432/db"
        async_url = settings.async_database_url
        assert async_url.startswith("postgresql+asyncpg://")
        assert "user:pass@host:5432/db" in async_url

    def test_async_url_with_none_database_url(self):
        """Test fallback when DATABASE_URL is None."""
        settings = Settings()
        settings.DATABASE_URL = None
        async_url = settings.async_database_url
        assert async_url == "sqlite+aiosqlite:///./portfolio.db"

    def test_async_url_preserves_sqlite(self):
        """Test that sqlite URL is preserved."""
        settings = Settings()
        settings.DATABASE_URL = "sqlite+aiosqlite:///./test.db"
        async_url = settings.async_database_url
        assert async_url == "sqlite+aiosqlite:///./test.db"


class TestGitHubOAuthConfig:
    """Tests for GitHub OAuth configuration."""

    def test_github_client_id_type(self):
        """Test GitHub client ID is string or None."""
        settings = Settings()
        assert settings.GITHUB_CLIENT_ID is None or isinstance(settings.GITHUB_CLIENT_ID, str)

    def test_github_client_secret_type(self):
        """Test GitHub client secret is string or None."""
        settings = Settings()
        assert settings.GITHUB_CLIENT_SECRET is None or isinstance(
            settings.GITHUB_CLIENT_SECRET, str
        )

    def test_github_redirect_uri_default(self):
        """Test GitHub redirect URI default."""
        settings = Settings()
        assert "callback" in settings.GITHUB_REDIRECT_URI

    def test_admin_github_id_type(self):
        """Test admin GitHub ID is string or None."""
        settings = Settings()
        assert settings.ADMIN_GITHUB_ID is None or isinstance(settings.ADMIN_GITHUB_ID, str)
