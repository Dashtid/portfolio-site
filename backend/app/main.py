"""
FastAPI main application
"""

import asyncio
import contextlib
from contextlib import asynccontextmanager
from datetime import UTC
from pathlib import Path

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIASGIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, PlainTextResponse

from app.api.v1 import (
    admin_panel,
    analytics,
    auth,
    companies,
    documents,
    education,
    errors,
    github,
    health,
    metrics,
    oss,
    projects,
    skills,
)
from app.config import settings
from app.core.security import decode_token
from app.database import Base, engine
from app.middleware import (
    CacheControlMiddleware,
    CompressionMiddleware,
    ErrorTrackingMiddleware,
    LoggingMiddleware,
    PerformanceMiddleware,
    limiter,
    rate_limit_exceeded_handler,
)
from app.services.github_service import github_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize Sentry for error tracking and performance monitoring.
# We explicitly enumerate integrations rather than relying on Sentry's
# auto-enable so the exact set is visible in code review and consistent
# across SDK versions. SqlalchemyIntegration adds spans per query (paired
# with Sprint 3 slow-query logging), HttpxIntegration covers outbound
# GitHub API calls, and AsyncioIntegration links task-spawn contexts so
# spans don't get orphaned across `asyncio.create_task` boundaries.
if settings.SENTRY_DSN and settings.ERROR_TRACKING_ENABLED:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        release=f"portfolio-api@{settings.APP_VERSION}",
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        send_default_pii=False,
        enable_tracing=True,
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
            SqlalchemyIntegration(),
            HttpxIntegration(),
            AsyncioIntegration(),
        ],
    )
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
    """

    @staticmethod
    def _oversize_response(limit: int) -> JSONResponse:
        return JSONResponse(
            status_code=413,
            content={
                "detail": (f"Request body too large. Maximum size is {limit // (1024 * 1024)} MB.")
            },
        )

    async def dispatch(self, request: Request, call_next):
        max_body_size = MAX_BODY_SIZE
        if request.url.path in BODY_SIZE_OVERRIDES and _bears_valid_token(request):
            max_body_size = BODY_SIZE_OVERRIDES[request.url.path]
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > max_body_size:
                    return self._oversize_response(max_body_size)
                # Trusted Content-Length already covers the entire body.
                return await call_next(request)
            except ValueError:
                # Fall through to the streaming counter.
                pass

        # Missing or invalid Content-Length: wrap the receive callable so we
        # tally each chunk as it streams in. Once the running total exceeds
        # the cap we short-circuit with 413 without buffering the rest.
        oversize = False
        bytes_seen = 0
        original_receive = request.receive

        async def counting_receive():
            nonlocal bytes_seen, oversize
            message = await original_receive()
            if message.get("type") == "http.request":
                body = message.get("body", b"")
                bytes_seen += len(body)
                if bytes_seen > max_body_size:
                    oversize = True
                    # Return an empty terminal frame so downstream sees a
                    # clean (but truncated) request stream while we abort.
                    return {"type": "http.request", "body": b"", "more_body": False}
            return message

        # Reassign the request's receive so handler body reads go through us.
        request._receive = counting_receive  # type: ignore[attr-defined]
        response = await call_next(request)
        if oversize:
            return self._oversize_response(max_body_size)
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


# Background task for periodic OAuth state cleanup
async def cleanup_oauth_states_periodically():
    """Periodically clean up expired OAuth states (every 5 minutes)"""
    # Local imports to avoid circular dependencies (noqa: PLC0415)
    from datetime import datetime  # noqa: PLC0415

    from sqlalchemy import delete  # noqa: PLC0415

    from app.database import AsyncSessionLocal  # noqa: PLC0415
    from app.models.oauth_state import OAuthState  # noqa: PLC0415

    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    delete(OAuthState).where(OAuthState.expires_at < datetime.now(UTC))
                )
                if result.rowcount > 0:  # type: ignore[attr-defined]
                    await session.commit()
                    logger.debug("Cleaned up %d expired OAuth states", result.rowcount)  # type: ignore[attr-defined]
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.exception("Error during OAuth state cleanup: %s", e)


# Data migrations (company/education/skill content corrections) have been
# extracted to scripts/migrate_data.py. Run once with:
#   cd backend && python -m scripts.migrate_data


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

    yield

    # Shutdown
    cleanup_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await cleanup_task

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
#   CORS -> Logging -> ErrorTracking -> Performance -> SecurityHeaders
#   -> CacheControl -> Compression -> BodySizeLimit -> SlowAPI -> routes
# BodySizeLimit sits just outside SlowAPI and the routes: nothing between
# it and the handlers reads request bodies, so DoS protection is preserved
# while its 413s pass through every header/logging layer on the way out.
# SlowAPI innermost means an oversized request costs a 413 without also
# consuming rate budget, while every request that reaches a handler has
# passed the limit check first.

# Rate limiting (D3-BE-01) — innermost. Without this middleware, slowapi's
# default_limits were dead config: only the ~15 decorated routes were
# limited and every undecorated one (admin mutations, /documents/upload,
# health) was unlimited, while startup logged "Rate limiting enabled".
# The ASGI variant (not SlowAPIMiddleware) is deliberate: the BaseHTTP
# variant silently swaps our async 429 handler for slowapi's default
# (sync_check_limits can't await), losing the Retry-After contract and
# the OBS-09 metrics counter. Decorator-limited routes are exempted by
# the middleware itself, so nothing is double-counted.
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(SlowAPIASGIMiddleware)

# Body size limit (DoS protection) — just outside the rate limiter
app.add_middleware(BodySizeLimitMiddleware)

# Compression (compress final response)
app.add_middleware(CompressionMiddleware, minimum_size=1000)

# Cache control headers
app.add_middleware(CacheControlMiddleware, max_age=300)

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
    ],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])
app.include_router(admin_panel.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(oss.router, prefix="/api/v1/admin", tags=["Admin OSS"])
app.include_router(auth.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(skills.router, prefix="/api/v1")
app.include_router(education.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
# Mount static files for document downloads (repo-baked assets, in-image)
app.mount("/static", StaticFiles(directory="static"), name="static")
# Admin-uploaded documents live under settings.UPLOAD_DIR — on Fly that's
# the persistent volume (/data/uploads/documents), NOT the image, so they
# survive deploys. check_dir=False: this mount is constructed at import
# time, before the directory exists — lifespan startup creates it.
app.mount(
    "/media",
    StaticFiles(directory=settings.UPLOAD_DIR, check_dir=False),
    name="media",
)
app.include_router(github.router, prefix="/api/v1/github", tags=["GitHub"])
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(errors.router, prefix="/api/v1")


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


# Security.txt endpoint (RFC 9116)
SECURITY_TXT_CONTENT = """# Security Policy for dashti.se API
# RFC 9116 compliant security.txt

Contact: mailto:security@dashti.se
Contact: https://www.linkedin.com/in/david-dashti/
Expires: 2026-12-31T23:59:59.000Z
Preferred-Languages: en, sv
Canonical: https://api.dashti.se/.well-known/security.txt

# Policy
# This is the API backend for dashti.se portfolio.
# If you discover a security vulnerability, please report it responsibly.
"""


@app.get("/.well-known/security.txt", include_in_schema=False)
@app.get("/security.txt", include_in_schema=False)
async def security_txt():
    """Serve security.txt for responsible disclosure (RFC 9116)"""
    return PlainTextResponse(SECURITY_TXT_CONTENT, media_type="text/plain")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
