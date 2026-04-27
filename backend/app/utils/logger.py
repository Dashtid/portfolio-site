"""
Centralized logging configuration with structured JSON output
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class CustomJsonFormatter(logging.Formatter):
    """JSON log formatter (stdlib only) emitting one JSON object per record."""

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
        return json.dumps(log_record)


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
