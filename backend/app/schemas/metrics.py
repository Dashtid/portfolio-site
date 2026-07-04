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
    # OBS-06 percentiles, computed on-demand from the bounded response-time
    # deque. Linear interpolation matches NumPy default so dashboards stay
    # consistent.
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    errors: int


class PerformanceMetrics(BaseModel):
    """Aggregated performance metrics returned by GET /metrics/."""

    total_requests: int
    endpoints: dict[str, EndpointStats] = Field(
        default_factory=dict,
        description=(
            "Per-endpoint statistics keyed by HTTP method + templated route "
            "(e.g. 'GET /api/v1/companies/{company_id}', not the resolved URL)"
        ),
    )
    status_codes: dict[int, int] = Field(
        default_factory=dict,
        description="Response status code counts keyed by HTTP status code",
    )
    # OBS-06: business counters. Anything that doesn't fit the per-endpoint
    # shape — rate_limit.hits, oauth.login.success/fail, geo_ip.cache.hit/miss,
    # github.api.call etc. — gets bumped via metrics.incr("name").
    counters: dict[str, int] = Field(
        default_factory=dict,
        description="Named business counters (rate-limit hits, OAuth outcomes, etc.)",
    )


class MetricsDisabled(BaseModel):
    """Response when metrics collection is disabled via settings."""

    message: str


class MetricsResetResponse(BaseModel):
    """Response for the /metrics/reset admin endpoint."""

    message: str
