"""
Metrics endpoint for performance monitoring and observability
"""

from fastapi import APIRouter, Depends

from app.config import settings
from app.core.deps import get_current_admin_user
from app.middleware.performance import get_metrics, reset_metrics
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=dict)
async def get_performance_metrics(
    current_user: User = Depends(get_current_admin_user),  # noqa: B008
):
    """
    Get current performance metrics (admin only)

    Returns aggregated statistics including:
    - Total request count
    - Response times per endpoint (avg, min, max)
    - Status code distribution
    - Error counts per endpoint

    Requires admin authentication to prevent information disclosure.
    """
    if not settings.METRICS_ENABLED:
        return {"message": "Metrics collection is disabled"}

    return get_metrics()


@router.post("/reset")
async def reset_performance_metrics(
    current_user: User = Depends(get_current_admin_user),  # noqa: B008
):
    """
    Reset performance metrics (admin only)

    Clears all accumulated metrics data.
    Useful for starting fresh after deployments or testing.
    Requires admin authentication.
    """
    if not settings.METRICS_ENABLED:
        return {"message": "Metrics collection is disabled"}

    reset_metrics()
    return {"message": f"Metrics reset successfully by {current_user.username}"}


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
