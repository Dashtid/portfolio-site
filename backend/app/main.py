"""
FastAPI main application
"""

import asyncio
import contextlib
from contextlib import asynccontextmanager
from datetime import UTC, timedelta
from pathlib import Path

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIASGIMiddleware
from starlette.datastructures import Headers, MutableHeaders
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.v1 import (
    admin_panel,
    analytics,
    auth,
    companies,
    cv,
    documents,
    education,
    github,
    health,
    metrics,
    oss,
    oss_public,
    projects,
    skills,
)
from app.config import settings
from app.core.security import decode_token
from app.core.sentry import attach_security_event_handler, sentry_options
from app.database import Base, engine
from app.middleware import (
    CacheControlMiddleware,
    CompressionMiddleware,
    ErrorTrackingMiddleware,
    LoggingMiddleware,
    OriginCheckMiddleware,
    PerformanceMiddleware,
    RouteLimitMiddleware,
    limiter,
    rate_limit_exceeded_handler,
)
from app.services.github_service import github_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

# How long analytics page views are kept. The dashboard's `days` query
# param is capped at 365 (app/api/v1/analytics.py), so nothing older is
# reachable through the UI — keeping it only grows the row the one
# unauthenticated writer on this API can create.
PAGE_VIEW_RETENTION = timedelta(days=400)

# Cadence of the background OSS-dashboard refresh. 6h is what the sync
# service's own httpx-lifecycle comment assumes, and at ~4 rate-limit
# points per run it is free against GitHub's 5000/hour budget.
OSS_REFRESH_INTERVAL_SECONDS = int(timedelta(hours=6).total_seconds())

# Sentry error tracking and performance monitoring. The options, and what
# they keep out of every event, transaction and breadcrumb, are in
# app/core/sentry.py. init runs before the routers are included below, so
# the integrations wrap every route.
if settings.SENTRY_DSN and settings.ERROR_TRACKING_ENABLED:
    sentry_sdk.init(**sentry_options())
    attach_security_event_handler()
    logger.info("Sentry initialized", extra={"environment": settings.ENVIRONMENT})


# Maximum request body size (5 MB) to prevent DoS attacks
MAX_BODY_SIZE = 5 * 1024 * 1024  # 5 MB

# Routes that legitimately accept larger bodies. The documents upload
# endpoint enforces its own 25 MB cap after reading the stream; the
# middleware allowance adds multipart-framing headroom on top so the
# handler's check stays the effective limit. Without this override the
# global 5 MB cap made the documented 25 MB upload limit unreachable.
# D3-BE-01: the override is only honoured for requests bearing a
# signature-valid JWT (see _bears_valid_token) — the upload endpoint is
# admin-only, but FastAPI parses the multipart body BEFORE the auth
# dependency runs, so without this gate an anonymous client could stream
# 26 MB per request at a route that would only reject it afterwards.
BODY_SIZE_OVERRIDES = {
    "/api/v1/documents/upload": 26 * 1024 * 1024,
}

# The routes that take a JSON body without authentication, capped far below
# MAX_BODY_SIZE for every caller: FastAPI parses the whole body before any
# route check runs, and their real bodies (a page-view beacon, or {} to
# /auth/refresh) are a few KB at most.
BODY_SIZE_CAPS = {
    "/api/v1/analytics/track/pageview": 16 * 1024,
    "/api/v1/auth/refresh": 16 * 1024,
}

# A request body gets BODY_READ_GRACE_SECONDS to start arriving, then must
# keep up an average of BODY_READ_MIN_RATE bytes a second: the deadline moves
# out with every byte read. uvicorn has no read timeout, so a client that
# trickled a declared body held its connection open indefinitely. The floor
# is about 260 kbit/s, so a 25 MB upload may take about 13 minutes.
BODY_READ_GRACE_SECONDS = 10.0
BODY_READ_MIN_RATE = 32 * 1024


def _bears_valid_token(request: Request) -> bool:
    """True when the request carries a JWT that passes signature+expiry.

    This is NOT the route's authorization check (no DB, no admin flag) —
    it is a cheap HMAC verification that a fabricated cookie cannot
    pass. Real authz still happens in the route dependencies; this gate
    only decides whether the large-body allowance applies, so the 26 MB
    parse budget is reserved for holders of a genuinely issued token.
    """
    token: str | None = None
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
    else:
        token = request.cookies.get("access_token")

    return bool(token and decode_token(token))


# Body Size Limit Middleware
class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request body size to prevent DoS attacks.

    Trusts the Content-Length header when it is present and parseable.
    Without that, the only way to enforce a cap is to count bytes as they
    arrive — otherwise a client sending Transfer-Encoding: chunked (or an
    unparseable Content-Length) gets through unbounded and downstream
    handlers read the whole payload into memory.

    A body must also arrive in time (BODY_READ_GRACE_SECONDS and
    BODY_READ_MIN_RATE); one that does not is answered 408.
    """

    @staticmethod
    def _oversize_response(limit: int) -> JSONResponse:
        if limit >= 1024 * 1024:
            size = f"{limit // (1024 * 1024)} MB"
        else:
            size = f"{limit // 1024} KB"
        return JSONResponse(
            status_code=413,
            content={"detail": f"Request body too large. Maximum size is {size}."},
        )

    @staticmethod
    def _timeout_response() -> JSONResponse:
        # The rest of the body may still be on its way, so the connection
        # cannot carry another request.
        return JSONResponse(
            status_code=408,
            content={"detail": "Request body not received in time."},
            headers={"Connection": "close"},
        )

    async def dispatch(self, request: Request, call_next):
        max_body_size = BODY_SIZE_CAPS.get(request.url.path, MAX_BODY_SIZE)
        if request.url.path in BODY_SIZE_OVERRIDES and _bears_valid_token(request):
            max_body_size = BODY_SIZE_OVERRIDES[request.url.path]
        content_length = request.headers.get("content-length")
        declared: int | None = None
        if content_length:
            try:
                declared = int(content_length)
            except ValueError:
                # Fall through to the streaming counter.
                declared = None
        # Parsed apart from call_next: a ValueError raised downstream must
        # propagate, not send the request through the app a second time.
        if declared is not None and declared > max_body_size:
            return self._oversize_response(max_body_size)
        if declared == 0 or (content_length is None and "transfer-encoding" not in request.headers):
            # No body to read.
            return await call_next(request)

        # A body is coming: wrap the receive callable so we tally each chunk
        # as it streams in (a missing or invalid Content-Length leaves no
        # other bound) and time its arrival. Past the cap or the deadline we
        # short-circuit with 413 or 408 without buffering the rest.
        oversize = False
        timed_out = False
        body_done = False
        bytes_seen = 0
        original_receive = request.receive
        started = asyncio.get_running_loop().time()

        async def counting_receive():
            nonlocal bytes_seen, oversize, timed_out, body_done
            if body_done:
                # Only a disconnect listener reads on; it has no deadline.
                return await original_receive()
            if oversize or timed_out:
                # After the terminal frame below, ASGI allows only
                # http.disconnect, so drop the rest of the body until it
                # comes. Anything listening for the disconnect (starlette
                # 1.8's FileResponse does) would otherwise get a body chunk,
                # and BaseHTTPMiddleware raises on it.
                message = await original_receive()
                while message.get("type") == "http.request":
                    message = await original_receive()
                return message
            deadline = started + BODY_READ_GRACE_SECONDS + bytes_seen / BODY_READ_MIN_RATE
            try:
                async with asyncio.timeout_at(deadline):
                    message = await original_receive()
            except TimeoutError:
                timed_out = True
                return {"type": "http.request", "body": b"", "more_body": False}
            if message.get("type") != "http.request":
                body_done = True
                return message
            bytes_seen += len(message.get("body", b""))
            if bytes_seen > max_body_size:
                oversize = True
                # Return an empty terminal frame so downstream sees a
                # clean (but truncated) request stream while we abort.
                return {"type": "http.request", "body": b"", "more_body": False}
            body_done = not message.get("more_body", False)
            return message

        # Reassign the request's receive so handler body reads go through us.
        request._receive = counting_receive
        response = await call_next(request)
        if oversize:
            return self._oversize_response(max_body_size)
        if timed_out:
            return self._timeout_response()
        return response


# Security Headers Middleware (OWASP 2025 compliant)
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Core security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        # "0" per current OWASP guidance: the legacy XSS auditor this header
        # controlled is gone from modern browsers, and in old ones "1;
        # mode=block" enabled side channels; CSP is the actual defense.
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # api.dashti.se is a SEPARATE host from dashti.se, so the site's
        # robots.txt "Disallow: /api/" does not apply to it -- and this host
        # serves no robots.txt at all (404 == crawl everything). Left alone,
        # Google can index /api/v1/companies etc., which republish the exact
        # prose the canonical pages carry: duplicate content competing with
        # the pages it was scraped from. X-Robots-Tag is the only signal that
        # travels with a JSON response.
        response.headers["X-Robots-Tag"] = "noindex, nofollow"

        # Cross-origin isolation headers (OWASP 2025)
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # Enhanced Permissions-Policy (OWASP 2025)
        permissions = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)

        # Set CSP based on environment: strict for production, relaxed for development.
        # Production drops cdn.jsdelivr.net entirely — /api/docs and /api/redoc are
        # disabled there (see FastAPI() init below) so Swagger UI no longer loads.
        if settings.ENVIRONMENT == "production":
            csp_directives = [
                "default-src 'self'",
                "script-src 'self'",
                "style-src 'self' https://fonts.googleapis.com",
                "font-src 'self' https://fonts.gstatic.com data:",
                "img-src 'self' data: https: blob:",
                # connect-src: GitHub data is fetched server-side via
                # httpx in app/services; no browser->api.github.com calls.
                # Keeping the whitelist narrow blocks XSS-exfiltration to
                # api.github.com if anything ever slips past the React-style
                # escaping in our Vue templates.
                "connect-src 'self' https://*.sentry.io",
                "frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com https://www.google.com/maps https://maps.google.com",
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "frame-ancestors 'none'",
                "upgrade-insecure-requests",
            ]
        else:
            # Development CSP - allows Vue.js hot-reload and devtools
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
                "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net data:",
                "img-src 'self' data: https: blob:",
                "connect-src 'self' https://cdn.jsdelivr.net https://*.sentry.io ws://localhost:* http://localhost:*",
                "frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com https://www.google.com/maps https://maps.google.com",
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "frame-ancestors 'none'",
            ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Strict-Transport-Security (HSTS) with preload - only for HTTPS in production
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        return response


# Scheme pin. Fly's proxy terminates TLS (fly.toml force_https redirects plain
# http) and uvicorn runs with --no-proxy-headers, so requests reach the app as
# http, and redirect_slashes builds its 307 Location from scope["scheme"].
class HTTPSSchemeMiddleware:
    """Mark production requests https before any inner layer reads the scheme.

    Outside production (local runs, tests) the scheme stays as it arrived.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if settings.ENVIRONMENT == "production":
            if scope["type"] == "http":
                scope["scheme"] = "https"
            elif scope["type"] == "websocket":
                scope["scheme"] = "wss"
        await self.app(scope, receive, send)


def _declares_body(scope: Scope) -> bool:
    """True when the request headers announce a body."""
    headers = Headers(scope=scope)
    if "transfer-encoding" in headers:
        return True
    try:
        return int(headers.get("content-length", "0")) > 0
    except ValueError:
        return True


class CloseUnreadBodyMiddleware:
    """Answer with Connection: close when the request body was not read to its end.

    uvicorn arms its keep-alive timer when a response completes, and a byte
    arriving afterwards cancels it without arming it again. A client whose
    declared body went unread (a GET with a Content-Length, a 404, 413 or
    429) could hold the connection open by sending one more byte.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not _declares_body(scope):
            await self.app(scope, receive, send)
            return
        body_read = False

        async def tracking_receive() -> Message:
            nonlocal body_read
            message = await receive()
            if message["type"] != "http.request" or not message.get("more_body", False):
                body_read = True
            return message

        async def closing_send(message: Message) -> None:
            if message["type"] == "http.response.start" and not body_read:
                message.setdefault("headers", [])
                MutableHeaders(scope=message)["Connection"] = "close"
            await send(message)

        await self.app(scope, tracking_receive, closing_send)


# Hosts the API answers in production. redirect_slashes builds its Location
# from the Host header, so an unchecked Host is reflected into the redirect.
API_HOSTS = ["api.dashti.se"]


class HostCheckMiddleware(TrustedHostMiddleware):
    """Answer 400 to a Host outside API_HOSTS in production.

    Fly's health checks reach the machine over its private network with
    the machine's private address as Host, so the two health routes, which
    never build a URL from the Host, skip the check. The match is exact:
    /api/v1/health/ is a slash redirect and is still checked. Outside
    production (local runs, tests) every Host passes.
    """

    EXEMPT_PATHS = frozenset({"/api/v1/health", "/api/v1/health/ready"})

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if settings.ENVIRONMENT != "production" or scope.get("path") in self.EXEMPT_PATHS:
            await self.app(scope, receive, send)
            return
        await super().__call__(scope, receive, send)


class CanonicalStaticFiles(StaticFiles):
    """StaticFiles that serves a file at its canonical path only.

    StaticFiles normalises the path before the lookup, so /x.pdf/, //x.pdf
    and /./x.pdf all served /x.pdf. Fly's [[statics]] matches the exact
    path, so those spellings reached the app, which sent the whole file.
    A path with an empty, "." or ".." segment is a 404 here instead.
    """

    def get_path(self, scope: Scope) -> str:
        if any(segment in ("", ".", "..") for segment in scope["path"].split("/")[1:]):
            raise HTTPException(status_code=404)
        return super().get_path(scope)


# Background task for periodic auth-row cleanup
async def cleanup_oauth_states_periodically():
    """Periodically purge expired OAuth states AND refresh-token rows (every 5 min).

    Refresh tokens: only EXPIRED rows are purged — revoked-but-unexpired
    rows must survive, they are what makes replay-of-a-rotated-token
    detection (RFC 6819 §5.2.2.3) work until natural expiry. Before this,
    the table grew one row per login + one per rotation, forever.
    """
    # Local imports to avoid circular dependencies (noqa: PLC0415)
    from datetime import datetime  # noqa: PLC0415

    from sqlalchemy import delete  # noqa: PLC0415

    from app.database import AsyncSessionLocal  # noqa: PLC0415
    from app.models.analytics import PageView  # noqa: PLC0415
    from app.models.oauth_state import OAuthState  # noqa: PLC0415
    from app.models.refresh_token import RefreshToken  # noqa: PLC0415

    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            async with AsyncSessionLocal() as session:
                now = datetime.now(UTC)
                states = await session.execute(
                    delete(OAuthState).where(OAuthState.expires_at < now)
                )
                tokens = await session.execute(
                    delete(RefreshToken).where(RefreshToken.expires_at < now)
                )
                # page_views is the only table an UNAUTHENTICATED caller can
                # grow, and it had no retention at all — every beacon since
                # launch was still resident. The analytics dashboard never
                # queries beyond 365 days (the `days` param is capped at 365
                # in analytics.py), so anything older is unreadable weight.
                views = await session.execute(
                    delete(PageView).where(PageView.created_at < now - PAGE_VIEW_RETENTION)
                )
                if (
                    states.rowcount > 0  # type: ignore[attr-defined]
                    or tokens.rowcount > 0  # type: ignore[attr-defined]
                    or views.rowcount > 0  # type: ignore[attr-defined]
                ):
                    await session.commit()
                    logger.debug(
                        "Cleanup: %d OAuth states, %d refresh tokens, %d page views",
                        states.rowcount,  # type: ignore[attr-defined]
                        tokens.rowcount,  # type: ignore[attr-defined]
                        views.rowcount,  # type: ignore[attr-defined]
                    )
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.exception("Error during auth-row cleanup: %s", e)


async def refresh_oss_dashboard_periodically():
    """Keep the public Open Source strip current (every 6 hours).

    Until 2026-08-25 the OSS dashboard refreshed ONLY when someone clicked
    the admin button. Nobody did for four weeks, and a NOT NULL crash in
    the refresh path (fixed in the same change) stayed invisible the whole
    time because its traceback had no audience — the homepage quietly
    served a frozen list of merged PRs. A proof surface that only updates
    when a human remembers is a proof surface that goes stale.

    6h matches the cadence the sync service already documents for its
    httpx-client lifecycle. Cheap: ~4 rate-limit points per run against
    5000/hour. The first run waits out the interval so boot stays fast and
    a crash-looping machine cannot hammer the GitHub API.

    Failures are logged and swallowed: a GitHub outage or an expired PAT
    must never take the API process down, and the strip keeps serving the
    last good rows from the database.
    """
    from app.database import AsyncSessionLocal  # noqa: PLC0415
    from app.services.oss_sync import oss_sync_service  # noqa: PLC0415

    while True:
        try:
            await asyncio.sleep(OSS_REFRESH_INTERVAL_SECONDS)
            if not settings.GITHUB_OSS_DASHBOARD_PAT:
                continue
            async with AsyncSessionLocal() as session:
                result = await oss_sync_service.refresh(session)
            logger.info(
                "Scheduled OSS dashboard refresh complete",
                extra={
                    "contributions_count": result.contributions_count,
                    "rate_limit_remaining": result.rate_limit_remaining,
                },
            )
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.exception("Scheduled OSS dashboard refresh failed: %s", e)


# Data migrations (the ~500-line hardcoded content-correction block that
# once ran in this lifespan) were extracted to scripts/migrate_data.py and
# later DELETED (2026-07-28): the script was invoked by nothing and its
# stale hardcoded map twice overwrote curated prod content (the Security+
# "Ongoing certification." incident, f5cc0df). Schema migrations run via
# scripts/migrate.py (fly release_command); content edits go through the
# admin API or one-off fly-ssh scripts.


# Validate CSP configuration to prevent dev CSP leaking to production
def validate_csp_configuration() -> None:
    """Validate that CSP configuration is appropriate for the environment."""
    if settings.ENVIRONMENT == "production":
        # In production, ensure DEBUG is disabled (which could indicate misconfiguration)
        if settings.DEBUG:
            logger.warning(
                "DEBUG is enabled in production environment! "
                "This may indicate a configuration issue. "
                "Development CSP policies are NOT being used (environment check is correct), "
                "but DEBUG should typically be disabled in production."
            )
        logger.info("CSP configured for production (strict mode)")
    else:
        # Non-production: using relaxed CSP with unsafe-inline/unsafe-eval
        logger.info(
            "CSP configured for development (relaxed mode with unsafe-inline/unsafe-eval)",
            extra={"environment": settings.ENVIRONMENT},
        )


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up application", extra={"version": settings.APP_VERSION})

    # Validate CSP configuration
    validate_csp_configuration()

    # The /media StaticFiles mount defers its directory check to the first
    # request (check_dir=False) and 500s while UPLOAD_DIR is missing, so
    # create it before serving traffic. On Fly it lives on the volume,
    # which is mounted by the time lifespan runs.
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    # D3-BE-04: schema creation on boot is a dev/test convenience only. In
    # production the schema is owned exclusively by Alembic via fly.toml's
    # release_command — create_all here both masked missing migrations
    # (new TABLES appeared silently while new COLUMNS on existing tables
    # did not, which is exactly how page_views.city drifted) and raced the
    # release migration on deploys.
    if settings.ENVIRONMENT != "production":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified (non-production convenience)")

    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_oauth_states_periodically())
    # Keep the public OSS strip fresh without anyone clicking a button.
    oss_refresh_task = asyncio.create_task(refresh_oss_dashboard_periodically())

    yield

    # Shutdown
    cleanup_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await cleanup_task

    oss_refresh_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await oss_refresh_task

    # Close GitHub service connection pool
    await github_service.close()
    logger.info("GitHub service connection pool closed")

    # PERF-10: close the shared OAuth httpx client.
    from app.api.v1.auth import close_oauth_client  # noqa: PLC0415

    await close_oauth_client()
    logger.info("OAuth httpx client closed")

    logger.info("Shutting down application")
    await engine.dispose()
    logger.info("Database connection closed")


# Create FastAPI instance.
# Swagger UI / ReDoc are off in production: the API is consumed exclusively by
# our own frontend, so the public endpoint catalogue is information disclosure
# with no upside. Disabling docs_url/redoc_url/openapi_url also lets the
# production CSP drop cdn.jsdelivr.net (the default Swagger UI asset host).
_docs_enabled = settings.ENVIRONMENT != "production"
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Portfolio API with Vue.js frontend",
    docs_url="/api/docs" if _docs_enabled else None,
    redoc_url="/api/redoc" if _docs_enabled else None,
    # openapi_url defaults to /openapi.json when not passed; setting it to None
    # disables the JSON schema endpoint, which is necessary because Swagger UI
    # alone is moot without the schema it renders.
    openapi_url=None if not _docs_enabled else "/openapi.json",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """FastAPI's 422 body without the rejected value in each error.

    The default handler echoed every error's "input": a response as large
    as the request body, and a lone surrogate in it made the JSON encoder
    raise, turning the 422 into a 500.
    """
    errors = [
        {key: value for key, value in error.items() if key != "input"} for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(errors)})


# Configure rate limiter
if settings.RATE_LIMIT_ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]
    logger.info("Rate limiting enabled", extra={"default_limit": settings.RATE_LIMIT_DEFAULT})

# Add middleware. Starlette's add_middleware PREPENDS: the LAST call added
# is the OUTERMOST layer. The previous ordering assumed first-added =
# outermost, which put CORS innermost — any response short-circuited by an
# outer layer (e.g. a BodySizeLimit 413) reached the browser without CORS
# headers, so frontend JS could not read the error. Layers below are added
# innermost-first; effective order outermost -> innermost:
#   CloseUnreadBody -> HTTPSScheme -> CORS -> Logging -> ErrorTracking
#   -> Performance -> SecurityHeaders -> HostCheck -> OriginCheck
#   -> CacheControl -> Compression -> BodySizeLimit -> RouteLimit
#   -> SlowAPI -> routes
# BodySizeLimit sits just outside the rate limiters (RouteLimit, SlowAPI)
# and the routes: nothing between it and the handlers reads request bodies,
# so DoS protection is preserved while its 413s pass through every
# header/logging layer on the way out. The limiters innermost means an
# oversized request costs a 413 without also consuming rate budget, while
# every request that reaches a handler has passed the limit check first.

# Rate limiting (D3-BE-01) — innermost. Without this middleware, slowapi's
# default_limits were dead config: only the ~15 decorated routes were
# limited and every undecorated one (admin mutations, /documents/upload,
# health) was unlimited, while startup logged "Rate limiting enabled".
# The ASGI variant (not SlowAPIMiddleware) is deliberate: the BaseHTTP
# variant silently swaps our async 429 handler for slowapi's default
# (sync_check_limits can't await), losing the Retry-After contract and
# the OBS-09 metrics counter. Decorator-limited routes are exempted by
# the middleware itself, so nothing is double-counted. RouteLimit, just
# outside it, checks those routes' own limits before the body is read.
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(SlowAPIASGIMiddleware)
    app.add_middleware(RouteLimitMiddleware)

# Body size limit (DoS protection) — just outside the rate limiter
app.add_middleware(BodySizeLimitMiddleware)

# Compression (compress final response)
app.add_middleware(CompressionMiddleware, minimum_size=1000)

# Cache control headers
app.add_middleware(CacheControlMiddleware, max_age=300)

# Origin check on cookie-authenticated writes — outside the body reads and
# rate limiters, so a refused request is never parsed and costs no budget.
app.add_middleware(OriginCheckMiddleware, allowed_origins=settings.CORS_ORIGINS)

# Host check (production) — inside the logging and security-header layers,
# so a rejected Host is still logged and its 400 carries the headers.
app.add_middleware(HostCheckMiddleware, allowed_hosts=API_HOSTS)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Performance monitoring
if settings.METRICS_ENABLED:
    app.add_middleware(PerformanceMiddleware)

# Error tracking
if settings.ERROR_TRACKING_ENABLED:
    app.add_middleware(ErrorTrackingMiddleware)

# Request/response logging
app.add_middleware(LoggingMiddleware)

# CORS — added last, therefore outermost: every response, including errors
# produced by any layer below, carries CORS headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
        "Cache-Control",
        "Pragma",
        # Sentry browserTracingIntegration attaches these to fetches whose URL
        # matches tracePropagationTargets (which includes api.dashti.se). If
        # they are missing here, the CORS preflight rejects EVERY API call the
        # moment a frontend DSN is configured.
        "sentry-trace",
        "baggage",
    ],
)

# Scheme pin — added after CORS, so outside it: the router and every layer
# see https in production.
app.add_middleware(HTTPSSchemeMiddleware)

# Outermost, so it sees the client's receive and every response, the 413s,
# 429s and 404s of the layers below included.
app.add_middleware(CloseUnreadBodyMiddleware)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])
app.include_router(admin_panel.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(cv.router, prefix="/api/v1/admin/cv", tags=["Admin CV"])
app.include_router(oss.router, prefix="/api/v1/admin", tags=["Admin OSS"])
app.include_router(oss_public.router, prefix="/api/v1/oss", tags=["OSS"])
app.include_router(auth.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(skills.router, prefix="/api/v1")
app.include_router(education.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
# Mount static files for document downloads (repo-baked assets, in-image)
app.mount("/static", CanonicalStaticFiles(directory="static"), name="static")
# Admin-uploaded documents live under settings.UPLOAD_DIR — on Fly that's
# the persistent volume (/data/uploads/documents), NOT the image, so they
# survive deploys. check_dir=False: this mount is constructed at import
# time, before the directory exists — lifespan startup creates it.
app.mount(
    "/media",
    CanonicalStaticFiles(directory=settings.UPLOAD_DIR, check_dir=False),
    name="media",
)
app.include_router(github.router, prefix="/api/v1/github", tags=["GitHub"])
app.include_router(analytics.router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Portfolio API is running!",
        "version": settings.APP_VERSION,
        # /api/docs is disabled in production; surfacing the URL only when it
        # actually resolves keeps the response honest for any clients reading it.
        "docs": "/api/docs" if _docs_enabled else None,
    }


# Security.txt endpoint (RFC 9116). Kept in step with the site's copy,
# frontend/public/.well-known/security.txt: every field but Canonical is the
# same, so a renewal changes both files. tests/test_security_txt.py fails 30
# days before Expires, and the weekly workflow
# .github/workflows/security-txt-expiry.yml checks both live copies.
SECURITY_TXT_CONTENT = """# Security Policy for dashti.se API
# RFC 9116 compliant security.txt

# Preferred: GitHub private vulnerability reporting.
Contact: https://github.com/Dashtid/portfolio-site/security/advisories/new
Contact: https://www.linkedin.com/in/david-dashti/
Expires: 2027-10-31T23:59:59.000Z
Preferred-Languages: en, sv
Canonical: https://api.dashti.se/.well-known/security.txt
Policy: https://github.com/Dashtid/portfolio-site/blob/main/SECURITY.md

# Policy
# This is the API backend for dashti.se portfolio.
# If you discover a security vulnerability, please report it responsibly
# using the contacts above.
"""


@app.get("/.well-known/security.txt", include_in_schema=False)
async def security_txt():
    """Serve security.txt for responsible disclosure (RFC 9116)"""
    return PlainTextResponse(SECURITY_TXT_CONTENT, media_type="text/plain")


# RFC 9116 section 3 lets the legacy top-level path redirect to /.well-known/.
# Serving the file there as well would fail section 2.5.2: its only Canonical
# field names the /.well-known/ URI, so a copy fetched from /security.txt
# "SHOULD NOT be trusted".
@app.get("/security.txt", include_in_schema=False)
async def security_txt_legacy():
    """Redirect the legacy path to /.well-known/security.txt (RFC 9116 section 3)"""
    return RedirectResponse("/.well-known/security.txt", status_code=301)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
