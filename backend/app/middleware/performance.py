"""
Performance monitoring middleware for tracking response times and metrics
"""

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import get_logger

logger = get_logger(__name__)


class PerformanceMetrics:
    """Thread-safe in-memory storage for performance metrics with bounded memory"""

    # Maximum number of response times to keep per endpoint (prevents memory exhaustion)
    MAX_RESPONSE_TIMES = 1000

    def __init__(self):
        self._lock = threading.Lock()
        self.request_count = defaultdict(int)
        # Use deque with maxlen to bound memory usage - keeps last N response times
        self.response_times: dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=self.MAX_RESPONSE_TIMES)
        )
        self.status_codes = defaultdict(int)
        self.errors = defaultdict(int)

    def record_request(self, method: str, path: str, duration_ms: float, status_code: int):
        """Record request metrics (thread-safe)"""
        endpoint = f"{method} {path}"

        with self._lock:
            self.request_count[endpoint] += 1
            self.response_times[endpoint].append(duration_ms)
            self.status_codes[status_code] += 1

            if status_code >= 400:
                self.errors[endpoint] += 1

    def get_stats(self) -> dict:
        """Get aggregated statistics (thread-safe)"""
        with self._lock:
            stats = {
                "total_requests": sum(self.request_count.values()),
                "endpoints": {},
                "status_codes": dict(self.status_codes),
            }

            for endpoint, times in self.response_times.items():
                if times:
                    stats["endpoints"][endpoint] = {
                        "count": self.request_count[endpoint],
                        "avg_response_time_ms": round(sum(times) / len(times), 2),
                        "min_response_time_ms": round(min(times), 2),
                        "max_response_time_ms": round(max(times), 2),
                        "errors": self.errors.get(endpoint, 0),
                    }

            return stats

    def reset(self):
        """Reset all metrics (thread-safe)"""
        with self._lock:
            self.request_count.clear()
            self.response_times.clear()
            self.status_codes.clear()
            self.errors.clear()


# Global metrics instance
metrics = PerformanceMetrics()


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics collection for metrics endpoint itself
        if request.url.path == "/api/v1/metrics":
            response: Response = await call_next(request)
            return response

        # Start timer
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Record metrics
            metrics.record_request(
                method=request.method,
                path=request.url.path,
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
                        "path": request.url.path,
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
                path=request.url.path,
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
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            # Record as 500 for unexpected exceptions
            metrics.record_request(
                method=request.method,
                path=request.url.path,
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
