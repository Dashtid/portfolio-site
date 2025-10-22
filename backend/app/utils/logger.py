"""
Centralized logging configuration with structured JSON output
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        # Add log level
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

        # Add logger name
        log_record['logger'] = record.name

        # Add file location
        log_record['file'] = f"{record.filename}:{record.lineno}"


class SensitiveDataFilter(logging.Filter):
    """Filter to mask sensitive data in logs"""

    SENSITIVE_KEYS = {
        'password', 'token', 'api_key', 'secret', 'authorization',
        'access_token', 'refresh_token', 'jwt', 'apikey', 'passwd'
    }

    def filter(self, record: logging.LogRecord) -> bool:
        """Mask sensitive data in log records"""
        if hasattr(record, 'msg') and isinstance(record.msg, dict):
            record.msg = self._mask_sensitive_data(record.msg)

        if hasattr(record, 'args') and isinstance(record.args, dict):
            record.args = self._mask_sensitive_data(record.args)

        return True

    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively mask sensitive fields in dictionaries"""
        if not isinstance(data, dict):
            return data

        masked_data = {}
        for key, value in data.items():
            # Check if key contains sensitive information
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                masked_data[key] = '***REDACTED***'
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


def setup_logger(name: str = None, level: str = "INFO") -> logging.Logger:
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
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(logger)s %(message)s',
        rename_fields={
            'levelname': 'level',
            'name': 'logger',
            'asctime': 'timestamp'
        }
    )

    handler.setFormatter(formatter)

    # Add sensitive data filter
    handler.addFilter(SensitiveDataFilter())

    # Add handler to logger
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get or create a logger instance

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    from app.config import settings
    return setup_logger(name, level=settings.LOG_LEVEL)
