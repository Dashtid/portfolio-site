"""
Error tracking middleware for exception handling and monitoring
"""

import sys
import traceback
from collections.abc import Callable

import sentry_sdk
from fastapi import Request, Response
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.core.ip_utils import get_client_ip
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _capture_to_sentry(exc: Exception, request: Request, status_code: int | None = None) -> None:
    """Send an exception to Sentry with request context as a tag/extra.

    Belt-and-braces alongside Sentry's StarletteIntegration: that integration
    catches exceptions Sentry's middleware sees, but our middleware order
    re-raises ours *outward* through several intermediate wrappers and we
    want a guaranteed capture point. capture_exception is a no-op when
    Sentry is not initialised (no DSN), so this is safe to call unconditionally.
    """
    request_id = getattr(request.state, "request_id", None)
    with sentry_sdk.new_scope() as scope:
        scope.set_tag("request_id", request_id or "unknown")
        scope.set_tag("http.method", request.method)
        scope.set_tag("http.path", request.url.path)
        if status_code is not None:
            scope.set_tag("http.status_code", str(status_code))
        sentry_sdk.capture_exception(exc)


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware for error tracking and exception monitoring"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response: Response = await call_next(request)
        except HTTPException as exc:
            # Log HTTP exceptions (4xx, 5xx)
            request_id = getattr(request.state, "request_id", "unknown")

            if exc.status_code >= 500:
                # Server errors - log as ERROR with traceback
                logger.exception(
                    f"HTTP {exc.status_code}: {exc.detail}",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": exc.status_code,
                        "error_detail": exc.detail,
                        "error_type": "HTTPException",
                    },
                )
                _capture_to_sentry(exc, request, status_code=exc.status_code)
            elif exc.status_code >= 400:
                # Client errors - log as WARNING
                logger.warning(
                    f"HTTP {exc.status_code}: {exc.detail}",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": exc.status_code,
                        "error_detail": exc.detail,
                    },
                )

            # Re-raise to let FastAPI handle the response
            raise
        except Exception as exc:
            # Unexpected exceptions - log as CRITICAL
            request_id = getattr(request.state, "request_id", "unknown")

            # Get stack trace
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stack_trace = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

            # Log the error with full context
            logger.critical(
                f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "stack_trace": stack_trace,
                    "client_ip": get_client_ip(request),
                    "user_agent": request.headers.get("user-agent"),
                },
            )
            _capture_to_sentry(exc, request, status_code=500)

            # Re-raise to let FastAPI handle the response
            raise
        else:
            return response


def track_error(error: Exception, context: dict | None = None):
    """
    Manually track an error with additional context

    Args:
        error: Exception to track
        context: Additional context dictionary
    """
    if not settings.ERROR_TRACKING_ENABLED:
        return

    exc_type, exc_value, exc_traceback = sys.exc_info()
    stack_trace = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    log_context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "stack_trace": stack_trace,
    }

    if context:
        log_context.update(context)

    logger.error("Tracked error: %s: %s", type(error).__name__, error, extra=log_context)

    # Ship to Sentry as well so call sites that route through track_error
    # are visible alongside middleware-captured exceptions. No-op if Sentry
    # isn't initialised.
    with sentry_sdk.new_scope() as scope:
        if context:
            for k, v in context.items():
                scope.set_extra(k, v)
        sentry_sdk.capture_exception(error)
