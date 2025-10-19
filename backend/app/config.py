"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Portfolio API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: Optional[str] = "sqlite+aiosqlite:///./portfolio.db"
    # For PostgreSQL (when ready):
    # DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/portfolio_db"

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    # GitHub OAuth (will be configured later)
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/github/callback"

    # Admin
    ADMIN_GITHUB_ID: Optional[str] = None  # Your GitHub user ID

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()