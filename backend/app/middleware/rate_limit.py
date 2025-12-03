"""
Rate limiting middleware using SlowAPI

Provides configurable rate limiting for API endpoints with different limits
for public and authenticated endpoints.
"""

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request.

    Handles X-Forwarded-For header for reverse proxy setups (Fly.io, Vercel).
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs: client, proxy1, proxy2
        # The first one is the original client
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


def get_user_or_ip(request: Request) -> str:
    """
    Get rate limit key based on authenticated user ID or client IP.

    This provides per-user rate limiting for authenticated requests,
    falling back to IP-based limiting for anonymous requests.
    """
    # Check for authenticated user in request state
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # Check for user ID in Authorization header (JWT)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # Use the token itself as key (will be same for same user)
        # This is a simplified approach - in production you might decode the token
        token_hash = hash(auth_header) % 10**8
        return f"token:{token_hash}"

    return get_client_ip(request)


# Create limiter instance with configurable defaults
limiter = Limiter(
    key_func=get_user_or_ip,
    default_limits=[settings.RATE_LIMIT_DEFAULT] if hasattr(settings, "RATE_LIMIT_DEFAULT") else ["100/minute"],
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

    retry_after = exc.detail.split("rate limit exceeded")[-1].strip() if exc.detail else "60"

    logger.warning(
        "Rate limit exceeded",
        extra={
            "client_ip": get_client_ip(request),
            "path": request.url.path,
            "method": request.method,
            "limit": str(exc.detail),
        },
    )

    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": retry_after,
        },
        headers={
            "Retry-After": retry_after.split()[-1] if retry_after else "60",
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
