"""
Health check endpoints for monitoring and load balancing
"""

import sys
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint
    Returns 200 OK if service is running
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "portfolio-api",
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):  # noqa: B008
    """
    Readiness check - verifies database connectivity
    Used by load balancers to determine if instance can receive traffic
    """
    try:
        # Test database connection
        await db.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "timestamp": datetime.now(UTC).isoformat(),
            "checks": {"database": "connected"},
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "timestamp": datetime.now(UTC).isoformat(),
            "checks": {"database": f"error: {str(e)}"},
        }


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check - verifies service is alive
    Used by orchestrators (Kubernetes, Docker Swarm) to restart dead containers
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(UTC).isoformat(),
        "python_version": sys.version,
    }
