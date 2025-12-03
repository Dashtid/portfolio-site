"""
Tests for logger utility
"""

import logging
from unittest.mock import patch

import pytest

from app.utils.logger import CustomJsonFormatter, SensitiveDataFilter, get_logger, setup_logger


class TestCustomJsonFormatter:
    """Tests for CustomJsonFormatter class."""

    def test_adds_timestamp(self):
        """Test that formatter adds timestamp to log record."""
        formatter = CustomJsonFormatter()
        log_record = {}
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0, msg="Test message", args=(), exc_info=None
        )
        formatter.add_fields(log_record, record, {})

        assert "timestamp" in log_record
        assert "Z" in log_record["timestamp"]  # ISO format with Z suffix

    def test_adds_log_level(self):
        """Test that formatter adds log level."""
        formatter = CustomJsonFormatter()
        log_record = {}
        record = logging.LogRecord(
            name="test", level=logging.WARNING, pathname="", lineno=0, msg="Test", args=(), exc_info=None
        )
        formatter.add_fields(log_record, record, {})

        assert log_record["level"] == "WARNING"

    def test_adds_logger_name(self):
        """Test that formatter adds logger name."""
        formatter = CustomJsonFormatter()
        log_record = {}
        record = logging.LogRecord(
            name="my_logger", level=logging.INFO, pathname="", lineno=0, msg="Test", args=(), exc_info=None
        )
        formatter.add_fields(log_record, record, {})

        assert log_record["logger"] == "my_logger"

    def test_adds_file_location(self):
        """Test that formatter adds file location."""
        formatter = CustomJsonFormatter()
        log_record = {}
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test_file.py", lineno=42, msg="Test", args=(), exc_info=None
        )
        formatter.add_fields(log_record, record, {})

        assert "file" in log_record
        assert "42" in log_record["file"]


class TestSensitiveDataFilter:
    """Tests for SensitiveDataFilter class."""

    def test_masks_password_key(self):
        """Test that password keys are masked."""
        filter_instance = SensitiveDataFilter()
        data = {"username": "test", "password": "secret123"}
        result = filter_instance._mask_sensitive_data(data)

        assert result["username"] == "test"
        assert result["password"] == "***REDACTED***"

    def test_masks_token_key(self):
        """Test that token keys are masked."""
        filter_instance = SensitiveDataFilter()
        data = {"access_token": "abc123", "user": "test"}
        result = filter_instance._mask_sensitive_data(data)

        assert result["access_token"] == "***REDACTED***"
        assert result["user"] == "test"

    def test_masks_api_key(self):
        """Test that api_key is masked."""
        filter_instance = SensitiveDataFilter()
        data = {"api_key": "secret-key-123"}
        result = filter_instance._mask_sensitive_data(data)

        assert result["api_key"] == "***REDACTED***"

    def test_masks_nested_sensitive_data(self):
        """Test that nested sensitive data is masked."""
        filter_instance = SensitiveDataFilter()
        data = {"user": {"name": "test", "password": "secret"}, "config": {"jwt": "token-value"}}
        result = filter_instance._mask_sensitive_data(data)

        assert result["user"]["name"] == "test"
        assert result["user"]["password"] == "***REDACTED***"
        assert result["config"]["jwt"] == "***REDACTED***"

    def test_masks_sensitive_data_in_list(self):
        """Test that sensitive data in lists is masked."""
        filter_instance = SensitiveDataFilter()
        data = {"users": [{"name": "user1", "secret": "secret1"}, {"name": "user2", "secret": "secret2"}]}
        result = filter_instance._mask_sensitive_data(data)

        assert result["users"][0]["name"] == "user1"
        assert result["users"][0]["secret"] == "***REDACTED***"
        assert result["users"][1]["secret"] == "***REDACTED***"

    def test_handles_non_dict_input(self):
        """Test that non-dict input is returned unchanged."""
        filter_instance = SensitiveDataFilter()
        result = filter_instance._mask_sensitive_data("not a dict")

        assert result == "not a dict"

    def test_filter_returns_true(self):
        """Test that filter method returns True (allows log through)."""
        filter_instance = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0, msg="Test", args=(), exc_info=None
        )

        assert filter_instance.filter(record) is True


class TestSetupLogger:
    """Tests for setup_logger function."""

    def test_creates_logger(self):
        """Test that setup_logger creates a logger."""
        logger = setup_logger("test_logger_1", "INFO")

        assert logger is not None
        assert logger.name == "test_logger_1"

    def test_sets_log_level(self):
        """Test that setup_logger sets correct log level."""
        logger = setup_logger("test_logger_2", "DEBUG")

        assert logger.level == logging.DEBUG

    def test_avoids_duplicate_handlers(self):
        """Test that setup_logger doesn't add duplicate handlers."""
        logger1 = setup_logger("test_logger_3", "INFO")
        handler_count_1 = len(logger1.handlers)

        logger2 = setup_logger("test_logger_3", "INFO")
        handler_count_2 = len(logger2.handlers)

        assert handler_count_1 == handler_count_2

    def test_handles_invalid_level(self):
        """Test that setup_logger handles invalid log level gracefully."""
        logger = setup_logger("test_logger_4", "INVALID_LEVEL")

        # Should default to INFO
        assert logger.level == logging.INFO


class TestGetLogger:
    """Tests for get_logger function."""

    def test_returns_logger(self):
        """Test that get_logger returns a logger."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.LOG_LEVEL = "INFO"
            logger = get_logger("test_get_logger")

            assert logger is not None
            assert logger.name == "test_get_logger"
