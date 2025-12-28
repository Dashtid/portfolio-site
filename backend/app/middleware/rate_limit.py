"""
Rate limiting middleware using SlowAPI

Provides configurable rate limiting for API endpoints with different limits
for public and authenticated endpoints.
"""

import hashlib

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings
from app.core.ip_utils import get_client_ip
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_user_or_ip(request: Request) -> str:
    """
    Get rate limit key based on authenticated user ID or client IP.

    This provides per-user rate limiting for authenticated requests,
    falling back to IP-based limiting for anonymous requests.
    """
    # Check for authenticated user in request state
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # Check for user ID in Authorization header (JWT) or cookie
    auth_header = request.headers.get("Authorization")
    access_cookie = request.cookies.get("access_token")

    if auth_header and auth_header.startswith("Bearer "):
        # Use SHA256 hash of token for secure, consistent rate limit key
        # Use 32 chars (128 bits) to reduce collision risk
        token_hash = hashlib.sha256(auth_header.encode()).hexdigest()[:32]
        return f"token:{token_hash}"

    if access_cookie:
        # Hash the cookie token for HTTP-only cookie auth
        # Use 32 chars (128 bits) to reduce collision risk
        token_hash = hashlib.sha256(access_cookie.encode()).hexdigest()[:32]
        return f"token:{token_hash}"

    return get_client_ip(request)


# Create limiter instance with configurable defaults
limiter = Limiter(
    key_func=get_user_or_ip,
    default_limits=[settings.RATE_LIMIT_DEFAULT]
    if hasattr(settings, "RATE_LIMIT_DEFAULT")
    else ["100/minute"],
    storage_uri=getattr(settings, "RATE_LIMIT_STORAGE_URI", None),
    strategy="fixed-window",
    headers_enabled=False,  # Disable header injection to avoid response issues
)


async def rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.

    Returns a JSON response with retry-after information.
    """
    # Type narrow to RateLimitExceeded
    if not isinstance(exc, RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )

    # Safely parse retry_after from exception detail
    retry_after = "60"  # Default fallback
    try:
        if exc.detail:
            # Try to extract time from "rate limit exceeded" message
            parts = exc.detail.split("rate limit exceeded")
            if len(parts) > 1:
                retry_after = parts[-1].strip() or "60"
    except (AttributeError, IndexError):
        pass  # Keep default

    logger.warning(
        "Rate limit exceeded",
        extra={
            "client_ip": get_client_ip(request),
            "path": request.url.path,
            "method": request.method,
            "limit": str(exc.detail) if exc.detail else "unknown",
        },
    )

    # Safely extract numeric retry value for header
    retry_header = "60"  # Default fallback
    try:
        if retry_after:
            parts = retry_after.split()
            if parts:
                retry_header = parts[-1]
    except (AttributeError, IndexError):
        pass  # Keep default

    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": retry_after,
        },
        headers={
            "Retry-After": retry_header,
            "X-RateLimit-Limit": str(exc.detail) if exc.detail else "",
        },
    )


# Predefined rate limit decorators for common use cases
# Usage: @rate_limit_auth on auth endpoints
rate_limit_auth = limiter.limit(
    getattr(settings, "RATE_LIMIT_AUTH", "5/minute"),
    error_message="Too many authentication attempts. Please try again later.",
)

# Usage: @rate_limit_api on general API endpoints
rate_limit_api = limiter.limit(
    getattr(settings, "RATE_LIMIT_API", "60/minute"),
    error_message="API rate limit exceeded. Please try again later.",
)

# Usage: @rate_limit_strict on sensitive endpoints
rate_limit_strict = limiter.limit(
    getattr(settings, "RATE_LIMIT_STRICT", "10/minute"),
    error_message="Rate limit exceeded for this endpoint.",
)

# Usage: @rate_limit_public on public read-only endpoints
rate_limit_public = limiter.limit(
    getattr(settings, "RATE_LIMIT_PUBLIC", "120/minute"),
    error_message="Too many requests. Please try again later.",
)
