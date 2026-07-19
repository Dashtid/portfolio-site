"""
Logging middleware for request/response tracking
"""

import re
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.ip_utils import get_client_ip
from app.utils.logger import get_logger, request_id_var

logger = get_logger(__name__)

# Accept only safe upstream IDs so a malicious client can't inject log
# control characters / poison structured-log queries via X-Request-ID. UUIDs
# and short opaque traceparent-style IDs are common; we accept up to 64 chars
# of [A-Za-z0-9_-].
_UPSTREAM_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

# Health-check paths get polled every few seconds by Fly's load balancer and
# any uptime monitoring. Skipping request/response log lines for them is
# PERF-07: it strips ~80% of the log volume on a quiet site, drops the
# allocations for the start/end pairs, and stops the noise from drowning
# out signal in Fly's tail. They still go through the rest of the pipeline
# (CORS, security headers, performance metrics) — only the log lines drop.
_SILENT_LOG_PREFIXES = ("/api/v1/health", "/api/health")

# D3-BE-02: query-param keys whose values are secrets. The GitHub OAuth
# callback arrives as GET /api/v1/auth/github/callback?code=...&state=...,
# so logging query params verbatim put a live authorization code and the
# CSRF state token into Fly's log stream on every login. SensitiveDataFilter
# only masks msg/args, not `extra` dicts — redaction has to happen here,
# before the dict reaches the logger. Matched case-insensitively.
_REDACTED_QUERY_PARAMS = frozenset(
    {"code", "state", "token", "access_token", "refresh_token", "client_secret"}
)


def _loggable_query_params(request: Request) -> dict[str, str]:
    """Query params with secret-bearing values replaced by a marker.

    Keeps the key visible (so log queries can still see *that* a code was
    presented) while dropping the value.
    """
    return {
        key: "[REDACTED]" if key.lower() in _REDACTED_QUERY_PARAMS else value
        for key, value in request.query_params.items()
    }


def _resolve_request_id(request: Request) -> str:
    """Reuse an upstream X-Request-ID if one is supplied and well-formed.

    Lets a CDN / load balancer / upstream service correlate a single user
    action across multiple backend hops. If absent or malformed we mint a
    fresh UUID — never trust unconstrained input into structured logs.
    """
    upstream = request.headers.get("X-Request-ID")
    if isinstance(upstream, str) and _UPSTREAM_REQUEST_ID_RE.match(upstream):
        return upstream
    return str(uuid.uuid4())


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Resolve request ID (upstream X-Request-ID if valid, else new UUID).
        request_id = _resolve_request_id(request)
        request.state.request_id = request_id
        # Publish to ContextVar so RequestIdFilter (in logger setup) can
        # tag every log line emitted during this request without each call
        # site needing to pass `extra={"request_id": ...}` manually.
        token = request_id_var.set(request_id)

        # PERF-07: opt out of request/response logging for high-frequency
        # health checks. We still set request_id and propagate it back in
        # the response header so on-call can correlate if they need to.
        silent = request.url.path.startswith(_SILENT_LOG_PREFIXES)

        # Start timer
        start_time = time.time()

        # Log incoming request (skipped for /health* to cut log volume).
        if not silent:
            logger.info(
                "Incoming request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": _loggable_query_params(request),
                    "client_ip": get_client_ip(request),
                    "user_agent": request.headers.get("user-agent"),
                },
            )

        # Process request
        try:
            try:
                response: Response = await call_next(request)

                # Calculate duration
                duration_ms = round((time.time() - start_time) * 1000, 2)

                # Log response. The ContextVar-backed RequestIdFilter also
                # injects request_id onto every record this request emits;
                # we keep it in the explicit extra here so downstream log
                # consumers and existing assertions still see it directly.
                if not silent:
                    logger.info(
                        "Request completed",
                        extra={
                            "request_id": request_id,
                            "method": request.method,
                            "path": request.url.path,
                            "status_code": response.status_code,
                            "duration_ms": duration_ms,
                        },
                    )

                # Add request ID to response headers
                response.headers["X-Request-ID"] = request_id
            except Exception as exc:
                # Calculate duration
                duration_ms = round((time.time() - start_time) * 1000, 2)

                # Always log errors, even on /health* — a failing health
                # check is a higher-priority signal than the success noise.
                logger.error(
                    "Request failed",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": duration_ms,
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                    },
                    exc_info=True,
                )

                # Re-raise exception
                raise
            else:
                return response
        finally:
            # Reset the ContextVar so log lines emitted *after* this request
            # (e.g. from a background task) don't inherit a stale ID.
            request_id_var.reset(token)
