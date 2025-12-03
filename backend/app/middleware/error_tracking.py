"""
Error tracking middleware for exception handling and monitoring
"""

import sys
import traceback
from collections.abc import Callable

from fastapi import Request, Response
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware for error tracking and exception monitoring"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)

        except HTTPException as exc:
            # Log HTTP exceptions (4xx, 5xx)
            request_id = getattr(request.state, "request_id", "unknown")

            if exc.status_code >= 500:
                # Server errors - log as ERROR
                logger.error(
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
                    "client_ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                },
            )

            # Re-raise to let FastAPI handle the response
            raise


def track_error(error: Exception, context: dict = None):
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

    logger.error(f"Tracked error: {type(error).__name__}: {str(error)}", extra=log_context)
