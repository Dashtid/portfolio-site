"""
Application configuration using Pydantic Settings
"""

import os
import warnings
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Marker for explicitly allowing insecure development mode
# Set SECRET_KEY=dev-mode-insecure to explicitly enable insecure development
_DEV_MODE_MARKER = "dev-mode-insecure"


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

    # CORS - environment-specific origins
    # In production, only production origins are allowed (override via CORS_ORIGINS env var)
    # In development, localhost origins are included
    CORS_ORIGINS: list = []

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v, info):
        """Parse and set CORS_ORIGINS based on environment"""
        environment = info.data.get("ENVIRONMENT", "development")

        if isinstance(v, str) and v:
            # Support comma-separated string from environment
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list) and v:
            return v

        # Default origins based on environment
        production_origins = [
            "https://dashti.se",
            "https://www.dashti.se",
        ]
        development_origins = [
            "http://localhost:3000",
            "http://localhost:5173",
        ]

        if environment == "production":
            return production_origins
        return development_origins + production_origins

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
    # SECRET_KEY MUST be set via environment variable (no fallback for security)
    # For development: set SECRET_KEY=dev-mode-insecure to explicitly enable insecure mode
    # For production: generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    SECRET_KEY: str | None = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes for security (2025 best practice)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days for refresh tokens

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str | None, info) -> str:
        """Ensure SECRET_KEY is properly configured"""
        environment = info.data.get("ENVIRONMENT", "development")

        # SECRET_KEY must always be explicitly set
        if v is None:
            raise ValueError(
                "SECRET_KEY environment variable is required. "
                "For development: set SECRET_KEY=dev-mode-insecure. "
                'For production: generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
            )

        if environment == "production":
            # In production, reject the dev mode marker
            if v == _DEV_MODE_MARKER:
                raise ValueError(
                    "SECRET_KEY=dev-mode-insecure is not allowed in production. "
                    'Generate a secure key with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
                )
            # Ensure key is sufficiently long
            if len(v) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")
        elif v == _DEV_MODE_MARKER:
            # Warn but allow explicit insecure mode in development
            warnings.warn(
                "Running with insecure development SECRET_KEY. Do not use in production!",
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
        if environment == "production":
            # Block localhost in production
            if "localhost" in v or "127.0.0.1" in v:
                raise ValueError(
                    "GITHUB_REDIRECT_URI must not use localhost in production. "
                    "Set GITHUB_REDIRECT_URI environment variable to your production callback URL."
                )
            # Require HTTPS in production
            if not v.startswith("https://"):
                raise ValueError("GITHUB_REDIRECT_URI must use HTTPS in production for security.")
        return v

    @model_validator(mode="after")
    def validate_oauth_redirect_domain(self):
        """
        Validate that GITHUB_REDIRECT_URI and FRONTEND_URL are consistent.

        In production, both should point to the same domain to prevent
        OAuth redirect attacks where a malicious domain could intercept tokens.
        """
        if self.ENVIRONMENT != "production":
            return self

        if not self.GITHUB_REDIRECT_URI or not self.FRONTEND_URL:
            return self

        try:
            redirect_parsed = urlparse(self.GITHUB_REDIRECT_URI)
            frontend_parsed = urlparse(self.FRONTEND_URL)

            redirect_domain = redirect_parsed.netloc.lower()
            frontend_domain = frontend_parsed.netloc.lower()

            # Extract base domain (handle subdomains like api.example.com and www.example.com)
            def get_base_domain(domain: str) -> str:
                parts = domain.split(".")
                if len(parts) >= 2:
                    return ".".join(parts[-2:])  # Get last 2 parts (e.g., example.com)
                return domain

            redirect_base = get_base_domain(redirect_domain)
            frontend_base = get_base_domain(frontend_domain)

            if redirect_base != frontend_base:
                warnings.warn(
                    f"GITHUB_REDIRECT_URI domain ({redirect_domain}) differs from "
                    f"FRONTEND_URL domain ({frontend_domain}). Ensure this is intentional.",
                    stacklevel=2,
                )
        except Exception:
            # Don't fail on parsing errors, just skip validation
            pass

        return self

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
