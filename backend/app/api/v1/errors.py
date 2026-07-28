"""
Frontend error logging endpoint

Receives errors from the frontend error tracker and logs them
for monitoring and debugging purposes.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Request

from app.middleware.rate_limit import get_client_ip, limiter
from app.schemas.errors import FrontendErrorCreate, FrontendErrorResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["errors"])


@router.post("/errors", response_model=FrontendErrorResponse)
@limiter.limit("30/minute")  # Rate limit to prevent log flooding
async def log_frontend_error(
    error: FrontendErrorCreate,
    request: Request,
) -> FrontendErrorResponse:
    """
    Log a frontend error for monitoring.

    This endpoint receives errors from the frontend error tracker
    and logs them with structured data for debugging and alerting.
    """
    # Get client info (uses trusted proxy validation from rate_limit module)
    client_ip = get_client_ip(request)

    error_id = str(uuid.uuid4())

    # Log the error with structured data. Extra keys must not collide with
    # LogRecord attributes: 'message', 'filename' and 'lineno' made
    # Logger.makeRecord raise KeyError, which 500'd this endpoint on EVERY
    # valid request while all tests mocked the logger (fixed 2026-07-28;
    # the src_* naming mirrors middleware/error_tracking.py).
    logger.error(
        "Frontend error received",
        extra={
            "error_id": error_id,
            "error_type": error.type,
            "error_message": error.message[:500],  # Truncate for log
            "url": error.url,
            "src_file": error.filename,
            "src_line": error.lineno,
            "src_col": error.colno,
            "component": error.component_name,
            "client_ip": client_ip,
            "user_agent": error.user_agent[:200] if error.user_agent else None,
            "timestamp": error.timestamp,
            "has_stack": bool(error.stack),
            "context": error.context,
        },
    )

    # In production, this could also:
    # - Store in database for analysis
    # - Send to Sentry/other error tracking
    # - Trigger alerts for critical errors

    return FrontendErrorResponse(
        id=error_id,
        received_at=datetime.now(UTC),
    )
