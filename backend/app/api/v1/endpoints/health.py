"""
Health check endpoints for monitoring and load balancing

Designed for compatibility with:
- UptimeRobot (https://uptimerobot.com)
- Better Stack (https://betterstack.com)
- Fly.io health checks
- Kubernetes liveness/readiness probes
"""

import sys
import time
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

router = APIRouter()

# Type alias for dependency injection (FastAPI 2025 best practice)
DbSession = Annotated[AsyncSession, Depends(get_db)]

# Track service start time for uptime calculation
_SERVICE_START_TIME = time.time()


def _get_uptime_seconds() -> float:
    """Calculate service uptime in seconds"""
    return round(time.time() - _SERVICE_START_TIME, 2)


def _format_uptime(seconds: float) -> str:
    """Format uptime as human-readable string"""
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")

    return " ".join(parts)


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint for uptime monitoring services.

    Returns 200 OK if service is running.
    Optimized for fast response - no database checks.

    Compatible with:
    - UptimeRobot keyword monitoring (checks for "healthy")
    - Better Stack heartbeat monitoring
    - Generic HTTP status monitoring
    """
    uptime_seconds = _get_uptime_seconds()

    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": uptime_seconds,
        "uptime_human": _format_uptime(uptime_seconds),
    }


@router.get("/health/ready")
async def readiness_check(db: DbSession, response: Response):
    """
    Readiness check - verifies database connectivity.

    Used by load balancers to determine if instance can receive traffic.
    Returns 503 Service Unavailable if database is not reachable.

    Compatible with:
    - Fly.io readiness checks
    - Kubernetes readiness probes
    - AWS ALB health checks
    """
    start_time = time.time()
    checks = {}
    all_healthy = True

    # Test database connection
    try:
        await db.execute(text("SELECT 1"))
        db_latency_ms = round((time.time() - start_time) * 1000, 2)
        checks["database"] = {
            "status": "connected",
            "latency_ms": db_latency_ms,
        }
    except Exception as e:
        all_healthy = False
        checks["database"] = {
            "status": "error",
            "error": str(e),
        }

    # Set appropriate status code
    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    uptime_seconds = _get_uptime_seconds()

    return {
        "status": "ready" if all_healthy else "not_ready",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "uptime_seconds": uptime_seconds,
        "checks": checks,
    }


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check - verifies service is alive.

    Used by orchestrators to restart dead containers.
    This is a minimal check - if this fails, the service should be restarted.

    Compatible with:
    - Kubernetes liveness probes
    - Docker health checks
    - Fly.io machine checks
    """
    uptime_seconds = _get_uptime_seconds()

    return {
        "status": "alive",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "python_version": sys.version.split()[0],
        "uptime_seconds": uptime_seconds,
        "uptime_human": _format_uptime(uptime_seconds),
    }


@router.get("/health/detailed")
async def detailed_health_check(db: DbSession, response: Response):
    """
    Detailed health check with all system information.

    Useful for debugging and comprehensive monitoring dashboards.
    Not recommended for high-frequency polling due to database check.
    """
    start_time = time.time()
    checks = {}
    all_healthy = True

    # Database check with latency
    try:
        db_start = time.time()
        await db.execute(text("SELECT 1"))
        db_latency_ms = round((time.time() - db_start) * 1000, 2)
        checks["database"] = {
            "status": "healthy",
            "latency_ms": db_latency_ms,
        }
    except Exception as e:
        all_healthy = False
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    # Calculate total response time
    total_latency_ms = round((time.time() - start_time) * 1000, 2)
    uptime_seconds = _get_uptime_seconds()

    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        },
        "runtime": {
            "python_version": sys.version.split()[0],
            "uptime_seconds": uptime_seconds,
            "uptime_human": _format_uptime(uptime_seconds),
        },
        "checks": checks,
        "response_time_ms": total_latency_ms,
    }
