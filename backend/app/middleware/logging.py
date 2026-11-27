"""
Logging middleware for request/response tracking

The request log lines ("Incoming request", "Request completed", "Request
failed") name no client: no address, no digest of one and no User-Agent.
client_log_fields() below gives the security events of
app/core/security_events.py their client fields; the 429 line of
app/middleware/rate_limit.py carries the address digest alone.
"""

import re
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.ip_utils import get_client_ip
from app.utils.ip_hash import hash_ip
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
# out signal in Fly's tail. The page-view beacon, sent for every page a
# visitor opens, is silent the same way. These paths still go through the
# rest of the pipeline (CORS, security headers, performance metrics) — only
# the log lines drop, and only while the response status is below 400.
_SILENT_LOG_PREFIXES = ("/api/v1/health", "/api/health", "/api/v1/analytics/track/pageview")

# D3-BE-02: query-param keys whose values are secrets. The GitHub OAuth
# callback arrives as GET /api/v1/auth/github/callback?code=...&state=...,
# so logging query params verbatim put a live authorization code and the
# CSRF state token into Fly's log stream on every login. SensitiveDataFilter
# only masks msg/args, not `extra` dicts — redaction has to happen here,
# before the dict reaches the logger. Matched case-insensitively. uvicorn's
# access line prints the raw query string, so the image runs --no-access-log.
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


# The first 64 characters of a User-Agent still name the client software
# (browser engine and OS, or the bot); the rest is mostly version detail.
_USER_AGENT_LOG_CHARS = 64


def client_log_fields(request: Request) -> dict[str, str | None]:
    """The client fields of a security event (app/core/security_events.py).

    The address only as its keyed digest (app/utils/ip_hash.py), the same
    for one address on every day, so the security events of one client can
    be traced, and the User-Agent cut to its first characters. No request
    log line carries either.
    """
    user_agent = request.headers.get("user-agent")
    return {
        "client_ip_hash": hash_ip(get_client_ip(request)),
        "user_agent": user_agent[:_USER_AGENT_LOG_CHARS] if user_agent else None,
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
        # health checks and the page-view beacon. We still set request_id
        # and propagate it back in the response header so on-call can
        # correlate if they need to.
        silent = request.url.path.startswith(_SILENT_LOG_PREFIXES)

        # Start timer
        start_time = time.time()

        # Log incoming request (skipped for the silent paths).
        if not silent:
            logger.info(
                "Incoming request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": _loggable_query_params(request),
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
                # A silent path is silent only while it succeeds: with
                # uvicorn's access log off, this is the one line a failing
                # request there (a readiness 503, a beacon's 422 or 429)
                # leaves in the request log.
                if not silent or response.status_code >= 400:
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

                # Always log errors, even on the silent paths — a failing
                # health check is a higher-priority signal than the success
                # noise.
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
