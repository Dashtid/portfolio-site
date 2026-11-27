"""
Security event log: one record per authentication decision
"""

from typing import Any

from starlette.requests import Request

from app.middleware.logging import client_log_fields
from app.middleware.performance import metrics
from app.utils.logger import get_logger

security_logger = get_logger("app.security")


def security_event(level: int, event: str, request: Request, **fields: Any) -> None:
    """Log `event` on the app.security logger and count it on the metrics page.

    The record's message and its `event` field name the decision, e.g.
    auth.login_success; it also carries the request path and the client
    fields of client_log_fields() in app/middleware/logging.py (the keyed
    IP digest, a cut User-Agent).
    Callers add identifiers and counts only, never a token, code or state
    value, and never a LogRecord attribute name (name, msg, args, ...) as
    a field: logging raises KeyError on those.
    """
    security_logger.log(
        level,
        event,
        extra={"event": event, "path": request.url.path, **client_log_fields(request), **fields},
        stacklevel=2,  # the record's file:line is the caller's
    )
    metrics.incr(event)
