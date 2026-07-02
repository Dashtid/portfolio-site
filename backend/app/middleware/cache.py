"""
Caching middleware for GET request responses
"""

from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# API path prefixes whose GET responses are anonymous, non-personalised, and
# safe to share across users via a CDN or browser cache. Anything under /api
# that is NOT on this list defaults to `private, no-store` plus `Vary:
# Cookie, Authorization` so per-user payloads (notably `/auth/me`, refresh
# rotations, admin analytics, /metrics) cannot leak between users via a
# shared cache.
PUBLIC_API_PREFIXES: tuple[str, ...] = (
    "/api/v1/projects",
    "/api/v1/companies",
    "/api/v1/skills",
    "/api/v1/education",
    "/api/v1/documents",
    "/api/v1/github/stats",
    "/api/v1/health",
)


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add Cache-Control headers to responses

    Helps browsers and CDNs cache static content appropriately while
    refusing to cache per-user or sensitive API responses.
    """

    def __init__(self, app, max_age: int = 3600):
        """
        Initialize cache control middleware

        Args:
            app: ASGI application
            max_age: Cache duration in seconds for public API reads (default 1 hour)
        """
        super().__init__(app)
        self.max_age = max_age

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)

        # Only cache successful GET requests
        if request.method == "GET" and 200 <= response.status_code < 300:
            path = request.url.path
            if self._is_static_content(path):
                # Static content - cache for longer (1 year)
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            elif path.startswith("/api/"):
                if self._is_public_api(path) and not self._is_authenticated(request):
                    response.headers["Cache-Control"] = f"public, max-age={self.max_age}"
                    response.headers["Vary"] = "Accept-Encoding, Cookie, Authorization"
                else:
                    # Authenticated requests to public endpoints must not be
                    # HTTP-cached: the admin UI does mutate-then-refetch on
                    # these same collection URLs, and a max-age'd browser
                    # cache serves the pre-edit list (RFC 9111 only
                    # invalidates the mutated URL, not the collection).
                    response.headers["Cache-Control"] = "private, no-store"
                    response.headers["Vary"] = "Cookie, Authorization"
            else:
                # Non-API HTML / SSR fallback - short browser cache
                response.headers["Cache-Control"] = "public, max-age=300"

        return response

    @staticmethod
    def _is_static_content(path: str) -> bool:
        """Check if path is static content"""
        static_extensions = {
            ".js",
            ".css",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".webp",
            ".ico",
            ".woff",
            ".woff2",
        }
        return any(path.endswith(ext) for ext in static_extensions)

    @staticmethod
    def _is_public_api(path: str) -> bool:
        """True if the path is an opted-in anonymous public read."""
        return any(path.startswith(prefix) for prefix in PUBLIC_API_PREFIXES)

    @staticmethod
    def _is_authenticated(request: Request) -> bool:
        """True if the request carries credentials (cookie or bearer)."""
        return bool(
            request.headers.get("authorization")
            or request.cookies.get("access_token")
            or request.cookies.get("refresh_token")
        )
