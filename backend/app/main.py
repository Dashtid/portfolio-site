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
        # Add certificate_url column to education table if it doesn't exist
        {
            "check": """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'education' AND column_name = 'certificate_url'
            """,
            "migrate": """
                ALTER TABLE education ADD COLUMN certificate_url VARCHAR(500);
            """,
            "description": "Add certificate_url column to education table",
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
                        # SQLite fallback for documents.order_index
                        if "documents" in migration["description"]:
                            result = await session.execute(text("PRAGMA table_info(documents)"))
                            columns = [row[1] for row in result.fetchall()]
                            if "order_index" not in columns:
                                await session.execute(
                                    text(
                                        "ALTER TABLE documents ADD COLUMN order_index INTEGER DEFAULT 0"
                                    )
                                )
                                await session.commit()
                                logger.info(
                                    "Migration applied (SQLite): %s", migration["description"]
                                )
                        # SQLite fallback for education.certificate_url
                        elif "education" in migration["description"]:
                            result = await session.execute(text("PRAGMA table_info(education)"))
                            columns = [row[1] for row in result.fetchall()]
                            if "certificate_url" not in columns:
                                await session.execute(
                                    text(
                                        "ALTER TABLE education ADD COLUMN certificate_url VARCHAR(500)"
                                    )
                                )
                                await session.commit()
                                logger.info(
                                    "Migration applied (SQLite): %s", migration["description"]
                                )
                    except Exception as sqlite_err:
                        logger.warning(
                            "Migration skipped: %s - %s", migration["description"], sqlite_err
                        )
                else:
                    logger.warning("Migration check failed: %s - %s", migration["description"], e)


# Data migration to fix company dates and titles (one-time migration)
async def migrate_company_data():
    """Update company dates and titles to correct values from LinkedIn data."""
    # Local imports (noqa: PLC0415)
    import uuid  # noqa: PLC0415
    from datetime import date  # noqa: PLC0415

    from sqlalchemy import select, update  # noqa: PLC0415

    from app.database import AsyncSessionLocal  # noqa: PLC0415
    from app.models.company import Company  # noqa: PLC0415

    # Mapping: name -> (title, start_date, end_date, order_index)
    company_updates = {
        "Hermes Medical Solutions": (
            "QA/RA & Security Specialist",
            date(2024, 5, 1),
            None,
            1,
        ),
        "Philips Healthcare": (
            "Incident Support Specialist, Nordics",
            date(2022, 3, 1),
            date(2024, 5, 31),
            2,
        ),
        "Karolinska University Hospital": (
            "Biomedical Engineer, Medical Imaging and Physiology",
            date(2021, 6, 1),
            date(2021, 12, 31),
            3,
        ),
        "SoftPro Medical Solutions": (
            "Master Thesis Student",
            date(2020, 10, 1),
            date(2021, 6, 30),
            4,
        ),
        "Södersjukhuset - SÖS": (
            "Biomedical Engineer, Radiology Department",
            date(2020, 6, 1),
            date(2021, 6, 30),
            5,
        ),
        "Södersjukhuset": (
            "Biomedical Engineer, Radiology Department",
            date(2020, 6, 1),
            date(2021, 6, 30),
            5,
        ),
        "Scania Engines": (
            "Technician, Engine Analysis",
            date(2016, 6, 1),
            date(2016, 8, 31),
            6,
        ),
        "Scania Group": (
            "Technician, Engine Analysis",
            date(2016, 6, 1),
            date(2016, 8, 31),
            6,
        ),
        "Finnish Defence Forces": (
            "Platoon Leader, 2nd Lieutenant",
            date(2014, 1, 1),
            date(2015, 1, 31),
            7,
        ),
    }

    async with AsyncSessionLocal() as session:
        # Update existing companies with titles and dates
        for name, (title, start_date, end_date, order_index) in company_updates.items():
            try:
                stmt = (
                    update(Company)
                    .where(Company.name == name)
                    .values(
                        title=title,
                        start_date=start_date,
                        end_date=end_date,
                        order_index=order_index,
                    )
                )
                result = await session.execute(stmt)
                if result.rowcount > 0:
                    logger.info("Updated company: %s", name)
            except Exception as e:
                logger.warning("Company update failed for %s: %s", name, e)

        # Rename Scania Engines to Scania Group
        stmt = update(Company).where(Company.name == "Scania Engines").values(name="Scania Group")
        result = await session.execute(stmt)
        if result.rowcount > 0:
            logger.info("Renamed Scania Engines to Scania Group")

        # Update Scania 2012 entry: rename and add logo
        stmt = (
            update(Company)
            .where(Company.name == "Scania Group (Early Career)")
            .values(
                name="Scania Group",
                logo_url="/images/scania.svg",
            )
        )
        result = await session.execute(stmt)
        if result.rowcount > 0:
            logger.info("Updated Scania 2012 entry with new name and logo")

        # If Scania 2012 doesn't exist yet, create it
        result = await session.execute(
            select(Company).where(
                Company.start_date == date(2012, 6, 1),
                Company.name == "Scania Group",
            )
        )
        if result.scalar_one_or_none() is None:
            # Check if old name exists
            result = await session.execute(
                select(Company).where(Company.name == "Scania Group (Early Career)")
            )
            if result.scalar_one_or_none() is None:
                scania_2012 = Company(
                    id=str(uuid.uuid4()),
                    name="Scania Group",
                    title="Technician, Engine Analysis",
                    description="Junior role at Scania working with engineers and technicians in second-line support, acquiring troubleshooting skills and understanding of production processes.",
                    location="Södertälje, Sweden",
                    start_date=date(2012, 6, 1),
                    end_date=date(2012, 8, 31),
                    website="https://www.scania.com",
                    logo_url="/images/scania.svg",
                    order_index=8,
                )
                session.add(scania_2012)
                logger.info("Added Scania 2012 entry")

        await session.commit()
        logger.info("Company data migration completed")


# Data migration to fix education dates and order (one-time migration)
async def migrate_education_data():
    """Update education dates and order to correct values from LinkedIn data."""
    # Local imports (noqa: PLC0415)
    from datetime import date  # noqa: PLC0415

    from sqlalchemy import update  # noqa: PLC0415

    from app.database import AsyncSessionLocal  # noqa: PLC0415
    from app.models.education import Education  # noqa: PLC0415

    # Mapping: institution -> (start_date, end_date, order, certificate_url)
    education_updates = {
        "KTH Royal Institute of Technology": (
            date(2018, 8, 1),
            date(2021, 6, 30),
            1,
            None,
        ),
        "Lund University": (
            date(2015, 8, 1),
            date(2018, 6, 30),
            2,
            None,
        ),
        "Företagsuniversitet": (
            date(2024, 10, 1),
            date(2024, 12, 31),
            3,
            "https://foretagsuniversitetet-yh.trueoriginal.com/utbildningsbevis-226768-datacourse-select-title-4436/?ref=linkedin-profile&lang=en",
        ),
    }

    async with AsyncSessionLocal() as session:
        for institution, (start_date, end_date, order, cert_url) in education_updates.items():
            try:
                update_values = {
                    "start_date": start_date,
                    "end_date": end_date,
                    "order": order,
                }
                if cert_url:
                    update_values["certificate_url"] = cert_url

                stmt = (
                    update(Education)
                    .where(Education.institution == institution)
                    .values(**update_values)
                )
                result = await session.execute(stmt)
                if result.rowcount > 0:
                    logger.info("Updated education: %s", institution)
            except Exception as e:
                logger.warning("Education update failed for %s: %s", institution, e)

        await session.commit()
        logger.info("Education data migration completed")


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
    await migrate_company_data()
    await migrate_education_data()

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
