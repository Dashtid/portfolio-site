"""
Metrics endpoint for performance monitoring and observability
"""
from fastapi import APIRouter, Depends
from app.middleware.performance import get_metrics, reset_metrics
from app.config import settings
from typing import Dict

router = APIRouter()


@router.get("/", response_model=Dict)
async def get_performance_metrics():
    """
    Get current performance metrics

    Returns aggregated statistics including:
    - Total request count
    - Response times per endpoint (avg, min, max)
    - Status code distribution
    - Error counts per endpoint
    """
    if not settings.METRICS_ENABLED:
        return {"message": "Metrics collection is disabled"}

    return get_metrics()


@router.post("/reset")
async def reset_performance_metrics():
    """
    Reset performance metrics

    Clears all accumulated metrics data.
    Useful for starting fresh after deployments or testing.
    """
    if not settings.METRICS_ENABLED:
        return {"message": "Metrics collection is disabled"}

    reset_metrics()
    return {"message": "Metrics reset successfully"}


@router.get("/health")
async def metrics_health():
    """
    Health check for metrics endpoint

    Returns basic system health information
    """
    return {
        "status": "healthy",
        "metrics_enabled": settings.METRICS_ENABLED,
        "error_tracking_enabled": settings.ERROR_TRACKING_ENABLED,
        "analytics_enabled": settings.ANALYTICS_ENABLED,
    }
