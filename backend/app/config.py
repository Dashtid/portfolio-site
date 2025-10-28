"""
Application configuration using Pydantic Settings
"""

import secrets

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Portfolio API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development, production

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str | None = "sqlite+aiosqlite:///./portfolio.db"

    @property
    def async_database_url(self) -> str:
        """
        Convert DATABASE_URL to async-compatible format.
        Fly.io provides postgres:// but SQLAlchemy async needs postgresql+asyncpg://
        """
        if self.DATABASE_URL is None:
            return "sqlite+aiosqlite:///./portfolio.db"

        url = self.DATABASE_URL
        # Convert postgres:// to postgresql+asyncpg://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        # Ensure postgresql:// becomes postgresql+asyncpg://
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        return url

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    # GitHub OAuth (will be configured later)
    GITHUB_CLIENT_ID: str | None = None
    GITHUB_CLIENT_SECRET: str | None = None
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/github/callback"

    # Admin
    ADMIN_GITHUB_ID: str | None = None  # Your GitHub user ID

    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Analytics
    ANALYTICS_ENABLED: bool = True
    ANALYTICS_SITE_ID: str | None = None  # Plausible/Umami site ID
    ANALYTICS_URL: str | None = None  # Analytics server URL

    # Error Tracking
    ERROR_TRACKING_ENABLED: bool = True
    ERROR_TRACKING_DSN: str | None = None  # Sentry DSN (optional)

    # Performance Monitoring
    METRICS_ENABLED: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
