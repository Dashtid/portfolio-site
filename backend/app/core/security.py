"""
Security utilities for JWT tokens (GitHub-OAuth-only — no password hashing).
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt.exceptions import PyJWTError

from app.config import settings


def _get_secret_key() -> str:
    """Get the secret key, asserting it's configured.

    The SECRET_KEY is validated at startup, so this should never fail at runtime.
    """
    if settings.SECRET_KEY is None:
        raise RuntimeError("SECRET_KEY is not configured")
    return settings.SECRET_KEY


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token"""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(to_encode, _get_secret_key(), algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """Create a JWT refresh token"""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    return jwt.encode(to_encode, _get_secret_key(), algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and verify a JWT token"""
    try:
        payload: dict[str, Any] = jwt.decode(
            token, _get_secret_key(), algorithms=[settings.ALGORITHM]
        )
    except PyJWTError:
        return None
    else:
        return payload
