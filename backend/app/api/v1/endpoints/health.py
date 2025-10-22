"""
Health check endpoints for monitoring and load balancing
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import sys

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
        "timestamp": datetime.utcnow().isoformat(),
        "service": "portfolio-api"
    }

@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check - verifies database connectivity
    Used by load balancers to determine if instance can receive traffic
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": "connected"
            }
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": f"error: {str(e)}"
            }
        }

@router.get("/health/live")
async def liveness_check():
    """
    Liveness check - verifies service is alive
    Used by orchestrators (Kubernetes, Docker Swarm) to restart dead containers
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": sys.version
    }
