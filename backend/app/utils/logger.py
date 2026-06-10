"""
Centralized logging configuration with structured JSON output
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# ContextVar holding the current request's correlation ID. Middleware sets it
# on every request (see app.middleware.logging); RequestIdFilter copies the
# current value onto each LogRecord so JSON logs always carry it without each
# call site having to pass `extra={"request_id": ...}` manually.
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# These attribute names are populated by logging.LogRecord itself. Anything
# NOT in this set on record.__dict__ came from `extra={...}` (or via a
# filter), so we serialise it into the JSON payload. Sourced from the
# stdlib `logging.LogRecord` constructor + `makeRecord` machinery.
_RESERVED_LOG_RECORD_ATTRS = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }
)


class CustomJsonFormatter(logging.Formatter):
    """JSON log formatter (stdlib only) emitting one JSON object per record.

    Anything passed via `extra={...}` (or attached by a logging Filter) gets
    serialised into the top-level JSON object alongside the fixed fields.
    Previously these were silently dropped, making structured log queries on
    Fly/Sentry essentially impossible — `extra={"request_id": ..., "user_id":
    ...}` ended up nowhere.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "file": f"{record.filename}:{record.lineno}",
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Serialise everything from `extra={...}`. We coerce non-JSON-native
        # values via str() rather than letting json.dumps raise — losing
        # exact representation is fine; losing the whole log line is not.
        for key, value in record.__dict__.items():
            if key in _RESERVED_LOG_RECORD_ATTRS or key.startswith("_"):
                continue
            if key in log_record:
                # Don't let `extra` clobber the fixed columns above.
                continue
            try:
                json.dumps(value)
                log_record[key] = value
            except (TypeError, ValueError):
                log_record[key] = repr(value)

        return json.dumps(log_record)


class RequestIdFilter(logging.Filter):
    """Inject the current request_id ContextVar onto every LogRecord.

    Set by LoggingMiddleware at the start of each request and consumed by
    CustomJsonFormatter via the regular `extra`-style attribute scan above.
    Logs emitted outside any request (startup, background tasks) get a
    `request_id` of None — better than silently lacking the field.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_var.get()
        return True


class SensitiveDataFilter(logging.Filter):
    """Filter to mask sensitive data in logs"""

    SENSITIVE_KEYS = {
        "password",
        "token",
        "api_key",
        "secret",
        "authorization",
        "access_token",
        "refresh_token",
        "jwt",
        "apikey",
        "passwd",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        """Mask sensitive data in log records"""
        if hasattr(record, "msg") and isinstance(record.msg, dict):
            record.msg = self._mask_sensitive_data(record.msg)

        if hasattr(record, "args") and isinstance(record.args, dict):
            record.args = self._mask_sensitive_data(record.args)

        return True

    def _mask_sensitive_data(self, data: Any) -> Any:
        """Recursively mask sensitive fields in dictionaries"""
        if not isinstance(data, dict):
            return data

        masked_data: dict[str, Any] = {}
        for key, value in data.items():
            # Check if key contains sensitive information
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                masked_data[key] = "***REDACTED***"
            elif isinstance(value, dict):
                masked_data[key] = self._mask_sensitive_data(value)
            elif isinstance(value, list):
                masked_data[key] = [
                    self._mask_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked_data[key] = value

        return masked_data


def setup_logger(name: str | None = None, level: str = "INFO") -> logging.Logger:
    """
    Setup and configure logger with JSON formatting

    Args:
        name: Logger name (defaults to root logger)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Set log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Create JSON formatter
    formatter = CustomJsonFormatter()

    handler.setFormatter(formatter)

    # Add sensitive data filter
    handler.addFilter(SensitiveDataFilter())
    # Inject the per-request correlation ID set by LoggingMiddleware.
    handler.addFilter(RequestIdFilter())

    # Add handler to logger
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get or create a logger instance

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    from app.config import settings  # noqa: PLC0415

    return setup_logger(name, level=settings.LOG_LEVEL)
