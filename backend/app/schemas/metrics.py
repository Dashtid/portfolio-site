"""
Pydantic schemas for the performance metrics endpoint.
"""

from pydantic import BaseModel, Field


class EndpointStats(BaseModel):
    """Per-endpoint aggregated statistics."""

    count: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    errors: int


class PerformanceMetrics(BaseModel):
    """Aggregated performance metrics returned by GET /metrics/."""

    total_requests: int
    endpoints: dict[str, EndpointStats] = Field(
        default_factory=dict,
        description="Per-endpoint statistics keyed by HTTP method + path",
    )
    status_codes: dict[int, int] = Field(
        default_factory=dict,
        description="Response status code counts keyed by HTTP status code",
    )


class MetricsDisabled(BaseModel):
    """Response when metrics collection is disabled via settings."""

    message: str


class MetricsResetResponse(BaseModel):
    """Response for the /metrics/reset admin endpoint."""

    message: str


class MetricsHealth(BaseModel):
    """Basic health check for metrics subsystem."""

    status: str
    metrics_enabled: bool
    error_tracking_enabled: bool
    analytics_enabled: bool
