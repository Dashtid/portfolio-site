"""
Application configuration using Pydantic Settings
"""

import os
import warnings

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Development-only fallback key (clearly marked as insecure)
_DEV_SECRET_KEY = "INSECURE-DEV-KEY-CHANGE-IN-PRODUCTION"


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Portfolio API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False  # Must explicitly enable in development
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

    # CORS - includes both development and production origins
    # Can be overridden with CORS_ORIGINS env var
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://dashti.se",
        "https://www.dashti.se",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string or list"""
        if isinstance(v, str):
            # Support comma-separated string from environment
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Frontend URL (for OAuth redirect)
    FRONTEND_URL: str = "http://localhost:3000"

    @field_validator("FRONTEND_URL")
    @classmethod
    def validate_frontend_url(cls, v: str, info) -> str:
        """Ensure FRONTEND_URL is HTTPS in production"""
        environment = info.data.get("ENVIRONMENT", "development")
        if environment == "production" and not v.startswith("https://"):
            warnings.warn(
                f"FRONTEND_URL '{v}' should use HTTPS in production",
                stacklevel=2,
            )
        return v

    # Security
    # SECRET_KEY should be set via environment variable in production
    # Falls back to dev key only in development mode
    SECRET_KEY: str = os.getenv("SECRET_KEY", _DEV_SECRET_KEY)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes for security (2025 best practice)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days for refresh tokens

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Ensure SECRET_KEY is properly configured for production"""
        # Get environment from values if available
        environment = info.data.get("ENVIRONMENT", "development")

        if environment == "production":
            # In production, reject insecure dev key
            if v == _DEV_SECRET_KEY:
                raise ValueError(
                    "SECRET_KEY must be set via environment variable in production. "
                    'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
                )
            # Ensure key is sufficiently long
            if len(v) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")
        elif v == _DEV_SECRET_KEY:
            # Warn in development but allow
            warnings.warn(
                "Using insecure development SECRET_KEY. Set SECRET_KEY environment variable for security.",
                stacklevel=2,
            )
        return v

    # GitHub OAuth (will be configured later)
    GITHUB_CLIENT_ID: str | None = None
    GITHUB_CLIENT_SECRET: str | None = None
    GITHUB_REDIRECT_URI: str = os.getenv(
        "GITHUB_REDIRECT_URI", "http://localhost:8000/api/v1/auth/github/callback"
    )

    @field_validator("GITHUB_REDIRECT_URI")
    @classmethod
    def validate_github_redirect(cls, v: str, info) -> str:
        """Ensure GITHUB_REDIRECT_URI is properly configured for production"""
        environment = info.data.get("ENVIRONMENT", "development")
        if environment == "production" and "localhost" in v:
            raise ValueError(
                "GITHUB_REDIRECT_URI must not use localhost in production. "
                "Set GITHUB_REDIRECT_URI environment variable to your production callback URL."
            )
        return v

    # Admin
    ADMIN_GITHUB_ID: str | None = None  # Your GitHub user ID

    # GitHub API Token (for authenticated requests and GraphQL)
    GITHUB_TOKEN: str | None = None

    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Analytics
    ANALYTICS_ENABLED: bool = True
    ANALYTICS_SITE_ID: str | None = None  # Plausible/Umami site ID
    ANALYTICS_URL: str | None = None  # Analytics server URL

    # Error Tracking (Sentry)
    ERROR_TRACKING_ENABLED: bool = True
    SENTRY_DSN: str | None = None  # Sentry DSN for error tracking
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # 10% of transactions for performance monitoring
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.1  # 10% of sampled transactions for profiling

    # Performance Monitoring
    METRICS_ENABLED: bool = True

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "100/minute"  # Default rate limit for all endpoints
    RATE_LIMIT_AUTH: str = "5/minute"  # Auth endpoints (login, token refresh)
    RATE_LIMIT_API: str = "60/minute"  # General API endpoints
    RATE_LIMIT_STRICT: str = "10/minute"  # Sensitive endpoints (password reset, etc.)
    RATE_LIMIT_PUBLIC: str = "120/minute"  # Public read-only endpoints
    RATE_LIMIT_STORAGE_URI: str | None = None  # Redis URI for distributed rate limiting

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
