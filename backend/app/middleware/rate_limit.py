"""
Rate limiting middleware using SlowAPI

Provides configurable rate limiting for API endpoints with different limits
for public and authenticated endpoints.
"""

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings
from app.core.ip_utils import get_client_ip
from app.core.security import decode_token
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_user_or_ip(request: Request) -> str:
    """
    Get rate limit key based on authenticated user ID or client IP.

    Only tokens that pass signature verification earn their own bucket,
    keyed by the token subject. The previous implementation hashed the
    raw header/cookie value without validating it, so a client rotating
    a junk `Authorization: Bearer <random>` header (or access_token
    cookie) minted a fresh bucket per request — a trivial bypass of
    every limit, including the auth brute-force one. Invalid or absent
    tokens now always fall through to the client IP.
    """
    # Check for authenticated user in request state
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # Verified JWT (header or HTTP-only cookie): key by subject, which is
    # stable across token refreshes — a per-token hash would hand out a
    # fresh budget on every rotation.
    token: str | None = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
    else:
        token = request.cookies.get("access_token")

    if token:
        payload = decode_token(token)
        subject = payload.get("sub") if payload else None
        if subject:
            return f"user:{subject}"

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


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.

    Returns a JSON response with retry-after information.
    """

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

    # OBS-09: bump a process-local counter so the admin /metrics endpoint
    # can surface rate-limit pressure without a log query. Imported lazily
    # to avoid a circular import (middleware/__init__.py imports both).
    try:
        from app.middleware.performance import metrics as _metrics  # noqa: PLC0415

        _metrics.incr("rate_limit.hits")
        _metrics.incr(f"rate_limit.hits.{request.method.lower()}")
    except Exception:
        # Counter bumping must never break the actual rate-limit response.
        pass

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

# Usage: @rate_limit_public on public read-only endpoints
rate_limit_public = limiter.limit(
    getattr(settings, "RATE_LIMIT_PUBLIC", "120/minute"),
    error_message="Too many requests. Please try again later.",
)

# NOTE (D3-BE-01): there is deliberately no decorator tier for
# /documents/upload. Decorated routes are exempted from the middleware's
# default limits, and the decorator only fires after auth dependencies
# pass — but FastAPI parses the multipart body BEFORE auth runs, so a
# decorator would exempt exactly the unauthenticated parse-flood traffic
# it was meant to throttle. The middleware default limit counts upload
# requests before any body parsing instead.
