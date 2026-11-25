"""
Metrics endpoint for performance monitoring and observability
"""

import logging

from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.core.deps import get_current_admin_user
from app.core.security_events import security_event
from app.middleware.performance import get_metrics, reset_metrics
from app.models.user import User
from app.schemas.metrics import (
    MetricsDisabled,
    MetricsResetResponse,
    PerformanceMetrics,
)

router = APIRouter()


@router.get("/", response_model=PerformanceMetrics | MetricsDisabled)
async def get_performance_metrics(
    current_user: User = Depends(get_current_admin_user),  # noqa: B008
) -> PerformanceMetrics | MetricsDisabled:
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
        return MetricsDisabled(message="Metrics collection is disabled")

    return PerformanceMetrics(**get_metrics())


@router.post("/reset", response_model=MetricsResetResponse | MetricsDisabled)
async def reset_performance_metrics(
    request: Request,
    current_user: User = Depends(get_current_admin_user),  # noqa: B008
) -> MetricsResetResponse | MetricsDisabled:
    """
    Reset performance metrics (admin only)

    Clears all accumulated metrics data.
    Useful for starting fresh after deployments or testing.
    Requires admin authentication.

    The counters it clears include the security-event and rate-limit
    counts, so the reset is itself a security event that records them.
    """
    if not settings.METRICS_ENABLED:
        return MetricsDisabled(message="Metrics collection is disabled")

    counters_before = get_metrics()["counters"]
    reset_metrics()
    security_event(
        logging.WARNING,
        "admin.metrics_reset",
        request,
        user_id=current_user.id,
        counters_before=counters_before,
    )
    return MetricsResetResponse(message=f"Metrics reset successfully by {current_user.username}")
