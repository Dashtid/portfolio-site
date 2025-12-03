"""
Caching middleware for GET request responses
"""

from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add Cache-Control headers to responses

    Helps browsers and CDNs cache static content appropriately
    """

    def __init__(self, app, max_age: int = 3600):
        """
        Initialize cache control middleware

        Args:
            app: ASGI application
            max_age: Cache duration in seconds (default 1 hour)
        """
        super().__init__(app)
        self.max_age = max_age

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Only cache successful GET requests
        if request.method == "GET" and 200 <= response.status_code < 300:
            # Add cache headers based on path
            if self._is_static_content(request.url.path):
                # Static content - cache for longer (1 year)
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            elif self._is_api_endpoint(request.url.path):
                # API endpoints - cache for configured duration
                response.headers["Cache-Control"] = f"public, max-age={self.max_age}"
                response.headers["Vary"] = "Accept-Encoding"
            else:
                # Default - short cache
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
    def _is_api_endpoint(path: str) -> bool:
        """Check if path is an API endpoint"""
        return path.startswith("/api/")
