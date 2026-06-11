"""
FastAPI main application
"""

import asyncio
import contextlib
from contextlib import asynccontextmanager
from datetime import UTC

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
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, PlainTextResponse

from app.api.v1 import analytics, auth, companies, education, github, projects, skills
from app.api.v1.endpoints import admin_panel, documents, errors, health, metrics
from app.config import settings
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
    def _oversize_response() -> JSONResponse:
        return JSONResponse(
            status_code=413,
            content={"detail": "Request body too large. Maximum size is 5 MB."},
        )

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > MAX_BODY_SIZE:
                    return self._oversize_response()
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
                if bytes_seen > MAX_BODY_SIZE:
                    oversize = True
                    # Return an empty terminal frame so downstream sees a
                    # clean (but truncated) request stream while we abort.
                    return {"type": "http.request", "body": b"", "more_body": False}
            return message

        # Reassign the request's receive so handler body reads go through us.
        request._receive = counting_receive  # type: ignore[attr-defined]
        response = await call_next(request)
        if oversize:
            return self._oversize_response()
        return response


# Security Headers Middleware (OWASP 2025 compliant)
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Core security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
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
                "connect-src 'self' https://api.github.com https://*.fly.dev https://*.sentry.io",
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
                "connect-src 'self' https://api.github.com https://*.fly.dev https://cdn.jsdelivr.net https://*.sentry.io ws://localhost:* http://localhost:*",
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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")

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

# Add middleware (order matters: first added = outermost layer)
# CORS must be outermost so error responses also get CORS headers (2025 best practice)
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

# Body size limit (DoS protection) - check early
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

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])
app.include_router(admin_panel.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(auth.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(skills.router, prefix="/api/v1")
app.include_router(education.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
# Mount static files for document downloads
app.mount("/static", StaticFiles(directory="static"), name="static")
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
Canonical: https://dashti-portfolio-backend.fly.dev/.well-known/security.txt

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
