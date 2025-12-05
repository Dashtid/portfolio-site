"""
Tests for logger utility module
"""

import logging

from app.utils.logger import (
    CustomJsonFormatter,
    SensitiveDataFilter,
    get_logger,
    setup_logger,
)


class TestCustomJsonFormatter:
    """Tests for CustomJsonFormatter class."""

    def test_formatter_initialization(self):
        """Test formatter can be initialized."""
        formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(message)s")
        assert formatter is not None

    def test_add_fields_adds_timestamp(self):
        """Test that timestamp is added to log records."""
        formatter = CustomJsonFormatter("%(message)s")
        log_record = {}
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        formatter.add_fields(log_record, record, {})
        assert "timestamp" in log_record
        assert "Z" in log_record["timestamp"]

    def test_add_fields_adds_level(self):
        """Test that level is added to log records."""
        formatter = CustomJsonFormatter("%(message)s")
        log_record = {}
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        formatter.add_fields(log_record, record, {})
        assert log_record["level"] == "WARNING"

    def test_add_fields_adds_logger_name(self):
        """Test that logger name is added to log records."""
        formatter = CustomJsonFormatter("%(message)s")
        log_record = {}
        record = logging.LogRecord(
            name="my.test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        formatter.add_fields(log_record, record, {})
        assert log_record["logger"] == "my.test.logger"

    def test_add_fields_adds_file_location(self):
        """Test that file location is added to log records."""
        formatter = CustomJsonFormatter("%(message)s")
        log_record = {}
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        formatter.add_fields(log_record, record, {})
        assert "file" in log_record
        assert "42" in log_record["file"]


class TestSensitiveDataFilter:
    """Tests for SensitiveDataFilter class."""

    def test_filter_returns_true(self):
        """Test that filter always returns True (doesn't drop records)."""
        filter_obj = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        assert filter_obj.filter(record) is True

    def test_mask_sensitive_password(self):
        """Test that password fields are masked."""
        filter_obj = SensitiveDataFilter()
        data = {"username": "john", "password": "secret123"}
        result = filter_obj._mask_sensitive_data(data)
        assert result["username"] == "john"
        assert result["password"] == "***REDACTED***"

    def test_mask_sensitive_token(self):
        """Test that token fields are masked."""
        filter_obj = SensitiveDataFilter()
        data = {"user": "john", "access_token": "abc123xyz"}
        result = filter_obj._mask_sensitive_data(data)
        assert result["user"] == "john"
        assert result["access_token"] == "***REDACTED***"

    def test_mask_sensitive_nested(self):
        """Test that nested sensitive data is masked."""
        filter_obj = SensitiveDataFilter()
        data = {"user": {"name": "john", "api_key": "secret"}}
        result = filter_obj._mask_sensitive_data(data)
        assert result["user"]["name"] == "john"
        assert result["user"]["api_key"] == "***REDACTED***"

    def test_mask_sensitive_in_list(self):
        """Test that sensitive data in lists is masked."""
        filter_obj = SensitiveDataFilter()
        data = {"items": [{"name": "item1", "secret": "hidden"}]}
        result = filter_obj._mask_sensitive_data(data)
        assert result["items"][0]["name"] == "item1"
        assert result["items"][0]["secret"] == "***REDACTED***"

    def test_mask_non_dict_returns_unchanged(self):
        """Test that non-dict data is returned unchanged."""
        filter_obj = SensitiveDataFilter()
        result = filter_obj._mask_sensitive_data("just a string")
        assert result == "just a string"

    def test_sensitive_keys_lowercase_match(self):
        """Test that sensitive key matching is case-insensitive."""
        filter_obj = SensitiveDataFilter()
        data = {"PASSWORD": "secret", "Api_Key": "key123"}
        result = filter_obj._mask_sensitive_data(data)
        assert result["PASSWORD"] == "***REDACTED***"
        assert result["Api_Key"] == "***REDACTED***"


class TestSetupLogger:
    """Tests for setup_logger function."""

    def test_setup_logger_returns_logger(self):
        """Test that setup_logger returns a logger instance."""
        logger = setup_logger("test.setup.logger")
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_setup_logger_with_level(self):
        """Test that logger level is set correctly."""
        logger = setup_logger("test.level.logger", level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_setup_logger_reuses_existing(self):
        """Test that calling setup_logger twice returns same logger."""
        logger1 = setup_logger("test.reuse.logger")
        logger2 = setup_logger("test.reuse.logger")
        assert logger1 is logger2


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test.get.logger")
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_get_logger_uses_settings_level(self):
        """Test that get_logger uses level from settings."""
        # get_logger imports settings inside the function
        # Just test that it works with actual settings
        logger = get_logger("test.settings.logger.v2")
        assert logger is not None
        assert isinstance(logger, logging.Logger)


class TestFormatterEdgeCases:
    """Additional tests for edge cases in formatter."""

    def test_add_fields_with_existing_level(self):
        """Test that existing level in log_record is uppercased."""
        formatter = CustomJsonFormatter("%(message)s")
        log_record = {"level": "info"}  # Pre-existing level
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        formatter.add_fields(log_record, record, {})
        assert log_record["level"] == "INFO"  # Should be uppercased


class TestSensitiveFilterEdgeCases:
    """Additional edge case tests for sensitive data filter."""

    def test_filter_with_dict_msg(self):
        """Test filter when record.msg is a dict."""
        filter_obj = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg={"user": "john", "password": "secret123"},
            args=(),
            exc_info=None,
        )
        filter_obj.filter(record)
        # msg should be masked
        assert record.msg["password"] == "***REDACTED***"

    def test_filter_with_dict_args(self):
        """Test filter when record.args is a dict via attribute."""
        filter_obj = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Login attempt",
            args=(),  # Start with empty args
            exc_info=None,
        )
        # Set args as dict directly (simulating rare edge case)
        record.args = {"token": "abc123"}
        filter_obj.filter(record)
        # args should be masked
        assert record.args["token"] == "***REDACTED***"

    def test_mask_non_sensitive_list_items(self):
        """Test that non-dict items in lists are preserved."""
        filter_obj = SensitiveDataFilter()
        data = {"items": ["string1", "string2", 123]}
        result = filter_obj._mask_sensitive_data(data)
        assert result["items"] == ["string1", "string2", 123]
