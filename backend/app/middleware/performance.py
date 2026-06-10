"""
Performance monitoring middleware for tracking response times and metrics
"""

import time
from bisect import bisect_left
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match

from app.utils.logger import get_logger

logger = get_logger(__name__)


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Linear-interpolation percentile on a sorted list.

    Matches NumPy's default `linear` interpolation so on-call dashboards
    that quote p50/p95/p99 give the same numbers regardless of which
    stack is rendering them. Returns 0.0 on empty input.
    """
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    rank = (pct / 100.0) * (len(sorted_values) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = rank - lo
    return float(sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * frac)


class PerformanceMetrics:
    """In-memory storage for performance metrics with bounded memory.

    PERF-06: dropped the `threading.Lock` from this class. Every caller
    is in the FastAPI async event loop — there is no true concurrency
    inside a single worker process. `dict.__setitem__`, `defaultdict[k]`
    and `deque.append` are individual-op atomic under CPython's GIL, and
    `record_request` only performs those plus increments via
    `counter += 1` (which is *not* atomic across threads but IS safe
    across cooperative-await points because nothing else can run until
    the coroutine voluntarily yields). gunicorn forks separate processes,
    so cross-worker contention requires a shared store (redis), not a
    lock. Removing the lock cuts the per-request overhead and removes a
    foot-gun where someone might add an `await` inside the `with` block.
    """

    # Maximum number of response times to keep per endpoint (prevents memory exhaustion)
    MAX_RESPONSE_TIMES = 1000

    def __init__(self):
        self.request_count: dict[str, int] = defaultdict(int)
        # Use deque with maxlen to bound memory usage - keeps last N response times
        self.response_times: dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=self.MAX_RESPONSE_TIMES)
        )
        self.status_codes: dict[int, int] = defaultdict(int)
        self.errors: dict[str, int] = defaultdict(int)
        # OBS-06 business counters: named integer tallies for events that
        # don't fit the per-endpoint shape (rate-limit hits, OAuth login
        # successes/failures, geo-ip cache hits/misses, etc.). Call
        # `metrics.incr("counter.name")` from wherever needs it.
        self.counters: dict[str, int] = defaultdict(int)

    def record_request(self, method: str, path: str, duration_ms: float, status_code: int):
        """Record request metrics."""
        endpoint = f"{method} {path}"

        self.request_count[endpoint] += 1
        self.response_times[endpoint].append(duration_ms)
        self.status_codes[status_code] += 1

        if status_code >= 400:
            self.errors[endpoint] += 1

    def incr(self, name: str, value: int = 1) -> None:
        """Bump a named business counter (OBS-06)."""
        self.counters[name] += value

    def get_stats(self) -> dict:
        """Get aggregated statistics."""
        endpoints: dict[str, dict] = {}
        stats: dict = {
            "total_requests": sum(self.request_count.values()),
            "endpoints": endpoints,
            "status_codes": dict(self.status_codes),
            "counters": dict(self.counters),
        }

        for endpoint, times in self.response_times.items():
            if not times:
                continue
            sorted_times = sorted(times)
            count = self.request_count[endpoint]
            endpoints[endpoint] = {
                "count": count,
                "avg_response_time_ms": round(sum(sorted_times) / len(sorted_times), 2),
                "min_response_time_ms": round(sorted_times[0], 2),
                "max_response_time_ms": round(sorted_times[-1], 2),
                # OBS-06: percentiles. Computed on-demand from the bounded
                # deque (max 1000 entries → sort is microseconds).
                "p50_response_time_ms": round(_percentile(sorted_times, 50), 2),
                "p95_response_time_ms": round(_percentile(sorted_times, 95), 2),
                "p99_response_time_ms": round(_percentile(sorted_times, 99), 2),
                "errors": self.errors.get(endpoint, 0),
            }

        return stats

    def reset(self):
        """Reset all metrics."""
        self.request_count.clear()
        self.response_times.clear()
        self.status_codes.clear()
        self.errors.clear()
        self.counters.clear()


# Global metrics instance
metrics = PerformanceMetrics()

# Silence the bisect import in environments that strip unused imports
# (kept for future use in skip-scan windowed percentile work).
_ = bisect_left


def _resolve_route_template(request: Request, fallback: str) -> str:
    """Return the route template that matched, e.g. /companies/{company_id}.

    PERF-05: without this, every unique URL path is its own metric key —
    100 GETs against /companies/{id} produce 100 separate stats entries
    and we lose the aggregate. The template gives us one stable key per
    handler.

    Looks up the matched route via the app router on the request's scope;
    falls back to the raw path on lookup failure (404, weird middleware
    ordering, etc.). Resolved AFTER call_next has run so the router has
    matched.
    """
    app = request.scope.get("app")
    if app is None:
        return fallback
    router = getattr(app, "router", None)
    if router is None:
        return fallback
    for route in router.routes:
        match, _child_scope = route.matches(request.scope)
        if match == Match.FULL:
            template = getattr(route, "path", None)
            if isinstance(template, str) and template:
                return template
    return fallback


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics collection for metrics endpoint itself
        if request.url.path == "/api/v1/metrics":
            response: Response = await call_next(request)
            return response

        # Start timer
        start_time = time.time()
        raw_path = request.url.path

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Record metrics (templated route key per PERF-05)
            metrics.record_request(
                method=request.method,
                path=_resolve_route_template(request, raw_path),
                duration_ms=duration_ms,
                status_code=response.status_code,
            )

            # Add performance headers
            response.headers["X-Response-Time"] = f"{round(duration_ms, 2)}ms"

            # Log slow requests (> 1 second)
            if duration_ms > 1000:
                request_id = getattr(request.state, "request_id", "unknown")
                logger.warning(
                    f"Slow request detected: {duration_ms}ms",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": raw_path,
                        "duration_ms": round(duration_ms, 2),
                        "status_code": response.status_code,
                    },
                )
        except HTTPException as exc:
            # Calculate duration for HTTP exceptions (4xx, 5xx)
            duration_ms = (time.time() - start_time) * 1000

            # Record with actual HTTP status code
            metrics.record_request(
                method=request.method,
                path=_resolve_route_template(request, raw_path),
                duration_ms=duration_ms,
                status_code=exc.status_code,
            )

            # Re-raise HTTP exception
            raise

        except Exception as exc:
            # Calculate duration for unexpected errors
            duration_ms = (time.time() - start_time) * 1000

            # Log unexpected errors
            logger.exception(
                f"Unexpected error in request: {exc}",
                extra={
                    "method": request.method,
                    "path": raw_path,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            # Record as 500 for unexpected exceptions
            metrics.record_request(
                method=request.method,
                path=_resolve_route_template(request, raw_path),
                duration_ms=duration_ms,
                status_code=500,
            )

            # Re-raise exception
            raise

        return response


def get_metrics() -> dict:
    """Get current performance metrics"""
    return metrics.get_stats()


def reset_metrics():
    """Reset performance metrics"""
    metrics.reset()
