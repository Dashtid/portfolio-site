"""
FastAPI main application
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import education
from app.api.v1 import auth, companies, github, projects  # , analytics
from app.api.v1.endpoints import documents, health, metrics
from app.config import settings
from app.database import Base, engine

# Import new middleware
from app.middleware import (
    CacheControlMiddleware,
    CompressionMiddleware,
    ErrorTrackingMiddleware,
    LoggingMiddleware,
    PerformanceMiddleware,
)

# Import models to ensure they're registered with Base
from app.utils.logger import get_logger

logger = get_logger(__name__)


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
        # Strict-Transport-Security (HSTS) - only for HTTPS in production
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up application", extra={"version": settings.APP_VERSION})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")
    yield
    # Shutdown
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

# Add middleware (order matters: first added = outermost layer)
# Compression should be outermost to compress final response
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

# CORS (should be close to the app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])
app.include_router(auth.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(education.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
# Mount static files for document downloads
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(github.router, prefix="/api/v1/github", tags=["GitHub"])
# app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])


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
