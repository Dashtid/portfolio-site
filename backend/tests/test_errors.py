"""
Tests for frontend error logging endpoint
"""

from datetime import UTC, datetime
from unittest.mock import patch

from fastapi.testclient import TestClient


# Helper to create valid base error data
def make_error_data(**overrides):
    """Create valid error data with defaults."""
    base = {
        "type": "error",
        "message": "Test error message",
        "timestamp": datetime.now(UTC).isoformat(),
        "url": "https://dashti.se/",
        "userAgent": "TestClient/1.0",
    }
    base.update(overrides)
    return base


class TestFrontendErrorEndpoint:
    """Tests for the frontend error logging endpoint."""

    def test_log_frontend_error_success(self, client: TestClient):
        """Test successful frontend error logging."""
        error_data = make_error_data(
            message="Uncaught TypeError: Cannot read property 'foo' of undefined",
            url="https://dashti.se/projects",
            filename="main.js",
            lineno=42,
            colno=15,
            stack="TypeError: Cannot read property 'foo' of undefined\n    at foo (main.js:42:15)",
            userAgent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        )

        with patch("app.api.v1.errors.logger") as mock_logger:
            response = client.post("/api/v1/errors", json=error_data)

            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "received_at" in data
            # Verify error was logged
            mock_logger.error.assert_called_once()

    def test_log_frontend_error_minimal(self, client: TestClient):
        """Test frontend error logging with minimal required fields."""
        error_data = make_error_data()

        with patch("app.api.v1.errors.logger"):
            response = client.post("/api/v1/errors", json=error_data)

            assert response.status_code == 200
            data = response.json()
            assert "id" in data

    def test_log_frontend_error_with_context(self, client: TestClient):
        """Test frontend error logging with additional context."""
        error_data = make_error_data(
            type="unhandledRejection",
            message="Promise rejection error",
            context={
                "component": "ProjectCard",
                "action": "loadData",
                "userId": "anonymous",
            },
        )

        with patch("app.api.v1.errors.logger") as mock_logger:
            response = client.post("/api/v1/errors", json=error_data)

            assert response.status_code == 200
            # Verify context was included in log
            call_kwargs = mock_logger.error.call_args[1]
            assert "context" in call_kwargs.get("extra", {})

    def test_log_frontend_error_real_logger_emits_record(self, client: TestClient):
        """Success path with the REAL logger — no mock.

        Guards the reserved-LogRecord-key crash: extra keys colliding with
        LogRecord attributes ('message', 'filename', 'lineno') make
        Logger.makeRecord raise KeyError, which 500'd this endpoint on
        every valid request while every other test mocked the logger.
        """
        import logging

        from app.api.v1.errors import logger as errors_logger

        records: list[logging.LogRecord] = []

        class _Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        handler = _Capture()
        errors_logger.addHandler(handler)
        try:
            response = client.post(
                "/api/v1/errors",
                json=make_error_data(
                    filename="main.js",
                    lineno=42,
                    colno=7,
                    context={"component": "RealLoggerTest"},
                ),
            )
        finally:
            errors_logger.removeHandler(handler)

        assert response.status_code == 200
        received = [r for r in records if r.getMessage() == "Frontend error received"]
        assert len(received) == 1
        # extras land on record.__dict__ (that is how the JSON formatter
        # scans them too); attribute access would trip mypy's LogRecord stub
        extras = received[0].__dict__
        assert extras["error_message"] == "Test error message"
        assert extras["src_file"] == "main.js"
        assert extras["src_line"] == 42
        assert extras["context"] == {"component": "RealLoggerTest"}

    def test_log_frontend_error_explicit_null_context_accepted(self, client: TestClient):
        """context: null is a realistic frontend payload and must pass."""
        error_data = make_error_data(context=None)

        with patch("app.api.v1.errors.logger"):
            response = client.post("/api/v1/errors", json=error_data)
            assert response.status_code == 200

    def test_context_non_serializable_rejected(self):
        """Direct model construction with a non-JSON value hits the
        serializability branch (unreachable over HTTP, where bodies are
        already JSON)."""
        import pytest
        from pydantic import ValidationError

        from app.schemas.errors import FrontendErrorCreate

        data = make_error_data(context={"bad": {1, 2}})
        with pytest.raises(ValidationError, match="JSON-serializable"):
            FrontendErrorCreate.model_validate(data)

    def test_log_frontend_error_context_at_key_limit_accepted(self, client: TestClient):
        """Context with exactly MAX_CONTEXT_KEYS keys passes validation."""
        error_data = make_error_data(context={f"key_{i}": i for i in range(10)})

        with patch("app.api.v1.errors.logger"):
            response = client.post("/api/v1/errors", json=error_data)
            assert response.status_code == 200

    def test_log_frontend_error_context_too_many_keys_rejected(self, client: TestClient):
        """Context with more than MAX_CONTEXT_KEYS keys is a 422, not silently trimmed.

        The old model_validate override was never invoked by FastAPI's body
        validation — this asserts the field_validator actually runs in the
        request path.
        """
        error_data = make_error_data(context={f"key_{i}": i for i in range(11)})

        with patch("app.api.v1.errors.logger") as mock_logger:
            response = client.post("/api/v1/errors", json=error_data)

            assert response.status_code == 422
            mock_logger.error.assert_not_called()

    def test_log_frontend_error_context_oversized_value_rejected(self, client: TestClient):
        """A single huge value is rejected by the serialized-size cap.

        This was the actual hole: key-count trimming (even had it run)
        allowed one key to carry megabytes into the logs, unauthenticated.
        """
        error_data = make_error_data(context={"payload": "X" * 6000})

        with patch("app.api.v1.errors.logger") as mock_logger:
            response = client.post("/api/v1/errors", json=error_data)

            assert response.status_code == 422
            mock_logger.error.assert_not_called()

    def test_log_frontend_error_context_under_size_cap_accepted(self, client: TestClient):
        """Context comfortably under the serialized-size cap passes."""
        error_data = make_error_data(context={"payload": "X" * 4000})

        with patch("app.api.v1.errors.logger"):
            response = client.post("/api/v1/errors", json=error_data)
            assert response.status_code == 200

    def test_context_size_cap_counts_utf8_bytes(self):
        """The cap measures encoded bytes, not characters."""
        import pytest
        from pydantic import ValidationError

        from app.schemas.errors import FrontendErrorCreate

        # 2000 three-byte characters -> 6000+ bytes but only ~2000 chars
        data = make_error_data(context={"payload": "€" * 2000})
        with pytest.raises(ValidationError, match="at most 5000 bytes"):
            FrontendErrorCreate.model_validate(data)

    def test_log_frontend_error_long_message_truncated(self, client: TestClient):
        """Test that long error messages are truncated in logs."""
        long_message = "X" * 1000  # 1000 character message

        error_data = make_error_data(message=long_message)

        with patch("app.api.v1.errors.logger") as mock_logger:
            response = client.post("/api/v1/errors", json=error_data)

            assert response.status_code == 200
            # Check that message was truncated to 500 chars in log
            call_kwargs = mock_logger.error.call_args[1]
            logged_message = call_kwargs.get("extra", {}).get("error_message", "")
            assert len(logged_message) <= 500

    def test_log_frontend_error_long_user_agent_truncated(self, client: TestClient):
        """Test that long user agent strings are truncated."""
        # User agent must be max 300 chars per schema
        long_ua = "Mozilla/5.0 " + "X" * 280

        error_data = make_error_data(userAgent=long_ua)

        with patch("app.api.v1.errors.logger") as mock_logger:
            response = client.post("/api/v1/errors", json=error_data)

            assert response.status_code == 200
            # Check that user_agent was truncated to 200 chars in log
            call_kwargs = mock_logger.error.call_args[1]
            logged_ua = call_kwargs.get("extra", {}).get("user_agent", "")
            assert len(logged_ua) <= 200

    def test_log_frontend_error_returns_uuid(self, client: TestClient):
        """Test that error ID is a valid UUID format."""
        import uuid

        error_data = make_error_data()

        with patch("app.api.v1.errors.logger"):
            response = client.post("/api/v1/errors", json=error_data)

            assert response.status_code == 200
            data = response.json()
            # Validate UUID format
            error_id = data["id"]
            uuid.UUID(error_id)  # Will raise if invalid

    def test_log_frontend_error_with_component_name(self, client: TestClient):
        """Test frontend error logging with component name."""
        error_data = make_error_data(
            type="vueError",
            message="Component rendering error",
            componentName="ProjectCard",
        )

        with patch("app.api.v1.errors.logger") as mock_logger:
            response = client.post("/api/v1/errors", json=error_data)

            assert response.status_code == 200
            call_kwargs = mock_logger.error.call_args[1]
            assert call_kwargs.get("extra", {}).get("component") == "ProjectCard"

    def test_log_frontend_error_missing_required_fields(self, client: TestClient):
        """Test frontend error logging fails without required fields."""
        error_data = {
            "type": "error",
            # Missing 'message', 'timestamp', 'url', 'userAgent' fields
        }

        response = client.post("/api/v1/errors", json=error_data)

        assert response.status_code == 422  # Validation error

    def test_log_frontend_error_logs_client_ip(self, client: TestClient):
        """Test that client IP is logged with the error."""
        error_data = make_error_data()

        with patch("app.api.v1.errors.logger") as mock_logger:
            response = client.post("/api/v1/errors", json=error_data)

            assert response.status_code == 200
            call_kwargs = mock_logger.error.call_args[1]
            extra = call_kwargs.get("extra", {})
            assert "client_ip" in extra

    def test_log_frontend_error_logs_has_stack(self, client: TestClient):
        """Test that presence of stack trace is logged."""
        error_data = make_error_data(stack="Error: Test\n    at foo:1:1")

        with patch("app.api.v1.errors.logger") as mock_logger:
            response = client.post("/api/v1/errors", json=error_data)

            assert response.status_code == 200
            call_kwargs = mock_logger.error.call_args[1]
            extra = call_kwargs.get("extra", {})
            assert extra.get("has_stack") is True

    def test_log_frontend_error_no_stack(self, client: TestClient):
        """Test that absence of stack trace is logged correctly."""
        error_data = make_error_data()

        with patch("app.api.v1.errors.logger") as mock_logger:
            response = client.post("/api/v1/errors", json=error_data)

            assert response.status_code == 200
            call_kwargs = mock_logger.error.call_args[1]
            extra = call_kwargs.get("extra", {})
            assert extra.get("has_stack") is False


class TestErrorsRouterConfiguration:
    """Tests for errors router configuration."""

    def test_router_exists(self):
        """Test that errors router is importable."""
        from app.api.v1.errors import router

        assert router is not None

    def test_router_has_correct_tags(self):
        """Test that router has correct tags."""
        from app.api.v1.errors import router

        assert "errors" in router.tags

    def test_logger_exists(self):
        """Test that logger is configured."""
        from app.api.v1.errors import logger

        assert logger is not None


class TestErrorTypesValidation:
    """Tests for error type validation."""

    def test_valid_error_type_error(self, client: TestClient):
        """Test 'error' type is accepted."""
        error_data = make_error_data(type="error")

        with patch("app.api.v1.errors.logger"):
            response = client.post("/api/v1/errors", json=error_data)
            assert response.status_code == 200

    def test_valid_error_type_unhandled_rejection(self, client: TestClient):
        """Test 'unhandledRejection' type is accepted."""
        error_data = make_error_data(type="unhandledRejection")

        with patch("app.api.v1.errors.logger"):
            response = client.post("/api/v1/errors", json=error_data)
            assert response.status_code == 200

    def test_valid_error_type_vue_error(self, client: TestClient):
        """Test 'vueError' type is accepted."""
        error_data = make_error_data(type="vueError")

        with patch("app.api.v1.errors.logger"):
            response = client.post("/api/v1/errors", json=error_data)
            assert response.status_code == 200

    def test_valid_error_type_manual(self, client: TestClient):
        """Test 'manual' type is accepted."""
        error_data = make_error_data(type="manual")

        with patch("app.api.v1.errors.logger"):
            response = client.post("/api/v1/errors", json=error_data)
            assert response.status_code == 200

    def test_invalid_error_type_rejected(self, client: TestClient):
        """Test invalid error type is rejected."""
        error_data = make_error_data(type="invalid-type")

        response = client.post("/api/v1/errors", json=error_data)
        assert response.status_code == 422
