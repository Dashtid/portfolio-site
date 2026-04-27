"""
Tests for logger utility module
"""

import json
import logging

from app.utils.logger import (
    CustomJsonFormatter,
    SensitiveDataFilter,
    get_logger,
    setup_logger,
)


def _record(
    name: str = "test",
    level: int = logging.INFO,
    pathname: str = "test.py",
    lineno: int = 1,
    msg: str = "Test message",
) -> logging.LogRecord:
    return logging.LogRecord(
        name=name,
        level=level,
        pathname=pathname,
        lineno=lineno,
        msg=msg,
        args=(),
        exc_info=None,
    )


class TestCustomJsonFormatter:
    """Tests for CustomJsonFormatter class."""

    def test_formatter_initialization(self):
        """Test formatter can be initialized."""
        formatter = CustomJsonFormatter()
        assert formatter is not None

    def test_add_fields_adds_timestamp(self):
        """Test that timestamp is added to log records."""
        formatter = CustomJsonFormatter()
        out = json.loads(formatter.format(_record()))
        assert "timestamp" in out
        assert out["timestamp"].endswith("Z")

    def test_add_fields_adds_level(self):
        """Test that level is added to log records."""
        formatter = CustomJsonFormatter()
        out = json.loads(formatter.format(_record(level=logging.WARNING)))
        assert out["level"] == "WARNING"

    def test_add_fields_adds_logger_name(self):
        """Test that logger name is added to log records."""
        formatter = CustomJsonFormatter()
        out = json.loads(formatter.format(_record(name="my.test.logger")))
        assert out["logger"] == "my.test.logger"

    def test_add_fields_adds_file_location(self):
        """Test that file location is added to log records."""
        formatter = CustomJsonFormatter()
        out = json.loads(formatter.format(_record(pathname="test.py", lineno=42)))
        assert "file" in out
        assert "42" in out["file"]


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

    def test_format_includes_exception_info(self):
        """Exception info from exc_info should be serialized into the JSON."""
        formatter = CustomJsonFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            import sys

            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="failed",
                args=(),
                exc_info=sys.exc_info(),
            )
        out = json.loads(formatter.format(record))
        assert "exception" in out
        assert "ValueError" in out["exception"]


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
