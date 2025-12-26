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
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1 import analytics, auth, companies, education, github, projects, skills
from app.api.v1.endpoints import documents, errors, health, metrics
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
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize Sentry for error tracking and performance monitoring
if settings.SENTRY_DSN and settings.ERROR_TRACKING_ENABLED:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        release=f"portfolio-api@{settings.APP_VERSION}",
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        send_default_pii=False,
        enable_tracing=True,
    )
    logger.info("Sentry initialized", extra={"environment": settings.ENVIRONMENT})


# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Security headers for production
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Set CSP based on environment: strict for production, relaxed for development
        if settings.ENVIRONMENT == "production":
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' https://cdn.jsdelivr.net",
                "style-src 'self' https://cdn.jsdelivr.net https://fonts.googleapis.com",
                "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net data:",
                "img-src 'self' data: https: blob:",
                "connect-src 'self' https://api.github.com https://*.fly.dev https://cdn.jsdelivr.net",
                "frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com https://www.google.com https://maps.google.com",
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "frame-ancestors 'none'",
            ]
        else:
            # Development CSP - allows Vue.js hot-reload and devtools
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
                "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net data:",
                "img-src 'self' data: https: blob:",
                "connect-src 'self' https://api.github.com https://*.fly.dev https://cdn.jsdelivr.net ws://localhost:* http://localhost:*",
                "frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com https://www.google.com https://maps.google.com",
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "frame-ancestors 'none'",
            ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Strict-Transport-Security (HSTS) - only for HTTPS in production
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
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
                if result.rowcount > 0:
                    await session.commit()
                    logger.debug("Cleaned up %d expired OAuth states", result.rowcount)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.exception("Error during OAuth state cleanup: %s", e)


# Database migration helper for adding columns to existing tables
async def run_migrations():
    """Run simple migrations to add missing columns to existing tables."""
    # Local imports to avoid circular dependencies (noqa: PLC0415)
    from sqlalchemy import text  # noqa: PLC0415

    from app.database import AsyncSessionLocal  # noqa: PLC0415

    migrations = [
        # Add order_index column to documents table if it doesn't exist
        {
            "check": """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'documents' AND column_name = 'order_index'
            """,
            "migrate": """
                ALTER TABLE documents ADD COLUMN order_index INTEGER DEFAULT 0;
                CREATE INDEX IF NOT EXISTS ix_documents_order_index ON documents (order_index);
            """,
            "description": "Add order_index column to documents table",
        },
    ]

    async with AsyncSessionLocal() as session:
        for migration in migrations:
            try:
                result = await session.execute(text(migration["check"]))
                if result.fetchone() is None:
                    # Column doesn't exist, run migration
                    for stmt in migration["migrate"].strip().split(";"):
                        if stmt.strip():
                            await session.execute(text(stmt.strip()))
                    await session.commit()
                    logger.info("Migration applied: %s", migration["description"])
            except Exception as e:
                # For SQLite, info schema doesn't exist - use PRAGMA instead
                if "information_schema" in str(e).lower() or "no such table" in str(e).lower():
                    try:
                        # SQLite fallback - check using PRAGMA
                        result = await session.execute(text("PRAGMA table_info(documents)"))
                        columns = [row[1] for row in result.fetchall()]
                        if "order_index" not in columns:
                            await session.execute(
                                text(
                                    "ALTER TABLE documents ADD COLUMN order_index INTEGER DEFAULT 0"
                                )
                            )
                            await session.commit()
                            logger.info("Migration applied (SQLite): %s", migration["description"])
                    except Exception as sqlite_err:
                        logger.warning(
                            "Migration skipped: %s - %s", migration["description"], sqlite_err
                        )
                else:
                    logger.warning("Migration check failed: %s - %s", migration["description"], e)


# Data migration to fix company dates (one-time migration)
async def migrate_company_dates():
    """Update company dates to correct values from LinkedIn data."""
    # Local imports (noqa: PLC0415)
    from sqlalchemy import text  # noqa: PLC0415

    from app.database import AsyncSessionLocal  # noqa: PLC0415

    # Mapping of company names to correct dates (name -> (start_date, end_date, order_index))
    company_updates = {
        "Hermes Medical Solutions": ("2024-06-01", None, 1),
        "Philips Healthcare": ("2022-03-01", "2024-05-31", 2),
        "Karolinska University Hospital": ("2021-06-01", "2021-12-31", 3),
        "SoftPro Medical Solutions": ("2020-10-01", "2021-06-30", 4),
        "Södersjukhuset - SÖS": ("2020-06-01", "2021-06-30", 5),
        "Södersjukhuset": ("2020-06-01", "2021-06-30", 5),
        "Scania Engines": ("2016-06-01", "2016-08-31", 6),
        "Scania Group": ("2016-06-01", "2016-08-31", 6),
        "Finnish Defence Forces": ("2014-01-01", "2015-01-31", 7),
    }

    async with AsyncSessionLocal() as session:
        for name, (start_date, end_date, order_index) in company_updates.items():
            try:
                if end_date:
                    await session.execute(
                        text(
                            "UPDATE companies SET start_date = :start, end_date = :end, "
                            "order_index = :order WHERE name = :name"
                        ),
                        {"start": start_date, "end": end_date, "order": order_index, "name": name},
                    )
                else:
                    await session.execute(
                        text(
                            "UPDATE companies SET start_date = :start, end_date = NULL, "
                            "order_index = :order WHERE name = :name"
                        ),
                        {"start": start_date, "order": order_index, "name": name},
                    )
            except Exception as e:
                logger.debug("Company update skipped for %s: %s", name, e)

        await session.commit()
        logger.info("Company dates migration completed")


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up application", extra={"version": settings.APP_VERSION})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")

    # Run migrations for existing tables
    await run_migrations()

    # Run data migrations
    await migrate_company_dates()

    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_oauth_states_periodically())

    yield

    # Shutdown
    cleanup_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await cleanup_task
    logger.info("Shutting down application")
    await engine.dispose()
    logger.info("Database connection closed")


# Create FastAPI instance
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Portfolio API with Vue.js frontend",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# Configure rate limiter
if settings.RATE_LIMIT_ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    logger.info("Rate limiting enabled", extra={"default_limit": settings.RATE_LIMIT_DEFAULT})

# Add middleware (order matters: first added = outermost layer)
# CORS must be outermost so error responses also get CORS headers (2025 best practice)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
)

# Compression (compress final response)
app.add_middleware(CompressionMiddleware, minimum_size=1000)

# Cache control headers
app.add_middleware(CacheControlMiddleware, max_age=3600)

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
        "docs": "/api/docs",
    }


# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME, "version": settings.APP_VERSION}


# Test endpoint for frontend connection
@app.get("/api/v1/test")
async def test_endpoint():
    return {
        "status": "success",
        "message": "Hello from FastAPI!",
        "data": {
            "framework": "FastAPI",
            "version": settings.APP_VERSION,
            "description": "Your portfolio backend is ready!",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
