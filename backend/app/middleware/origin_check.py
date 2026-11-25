"""
Origin check for state-changing requests that carry an auth cookie
"""

from starlette.datastructures import Headers
from starlette.requests import cookie_parser
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.utils.logger import get_logger

logger = get_logger(__name__)

UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
AUTH_COOKIES = ("access_token", "refresh_token")


class OriginCheckMiddleware:
    """Answer 403 to a cookie-authenticated unsafe request from a foreign origin.

    SameSite=Lax keeps the auth cookies off cross-site requests, but a page
    on any other *.dashti.se host is same-site, and a form POST, an upload
    or a bodyless POST from it needs no CORS preflight. So a request that
    carries an auth cookie needs an Origin in allowed_origins (the CORS
    list) or Sec-Fetch-Site: same-origin. Browsers send Origin on these
    methods; without it, Sec-Fetch-Site same-site or cross-site is refused,
    and a request with neither header comes from a non-browser client that
    holds the cookie itself. A request authenticated only by its
    Authorization header carries no ambient credential and passes.
    """

    def __init__(self, app: ASGIApp, allowed_origins: list[str]) -> None:
        self.app = app
        self.allowed_origins = frozenset(allowed_origins)

    def _allowed(self, headers: Headers) -> bool:
        cookies = cookie_parser(headers.get("cookie", ""))
        if not any(cookies.get(name) for name in AUTH_COOKIES):
            return True
        if headers.get("sec-fetch-site") == "same-origin":
            return True
        origin = headers.get("origin")
        if origin is not None:
            return origin in self.allowed_origins
        return headers.get("sec-fetch-site") in (None, "none")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] in UNSAFE_METHODS:
            headers = Headers(scope=scope)
            if not self._allowed(headers):
                logger.warning(
                    "Cross-origin request refused",
                    extra={
                        "method": scope["method"],
                        "path": scope["path"],
                        "origin": (headers.get("origin") or "")[:200],
                        "sec_fetch_site": (headers.get("sec-fetch-site") or "")[:32],
                    },
                )
                response = JSONResponse({"detail": "Cross-origin request refused"}, status_code=403)
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
