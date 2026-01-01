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

        with patch("app.api.v1.endpoints.errors.logger") as mock_logger:
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

        with patch("app.api.v1.endpoints.errors.logger"):
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

        with patch("app.api.v1.endpoints.errors.logger") as mock_logger:
            response = client.post("/api/v1/errors", json=error_data)

            assert response.status_code == 200
            # Verify context was included in log
            call_kwargs = mock_logger.error.call_args[1]
            assert "context" in call_kwargs.get("extra", {})

    def test_log_frontend_error_long_message_truncated(self, client: TestClient):
        """Test that long error messages are truncated in logs."""
        long_message = "X" * 1000  # 1000 character message

        error_data = make_error_data(message=long_message)

        with patch("app.api.v1.endpoints.errors.logger") as mock_logger:
            response = client.post("/api/v1/errors", json=error_data)

            assert response.status_code == 200
            # Check that message was truncated to 500 chars in log
            call_kwargs = mock_logger.error.call_args[1]
            logged_message = call_kwargs.get("extra", {}).get("message", "")
            assert len(logged_message) <= 500

    def test_log_frontend_error_long_user_agent_truncated(self, client: TestClient):
        """Test that long user agent strings are truncated."""
        # User agent must be max 300 chars per schema
        long_ua = "Mozilla/5.0 " + "X" * 280

        error_data = make_error_data(userAgent=long_ua)

        with patch("app.api.v1.endpoints.errors.logger") as mock_logger:
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

        with patch("app.api.v1.endpoints.errors.logger"):
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

        with patch("app.api.v1.endpoints.errors.logger") as mock_logger:
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

        with patch("app.api.v1.endpoints.errors.logger") as mock_logger:
            response = client.post("/api/v1/errors", json=error_data)

            assert response.status_code == 200
            call_kwargs = mock_logger.error.call_args[1]
            extra = call_kwargs.get("extra", {})
            assert "client_ip" in extra

    def test_log_frontend_error_logs_has_stack(self, client: TestClient):
        """Test that presence of stack trace is logged."""
        error_data = make_error_data(stack="Error: Test\n    at foo:1:1")

        with patch("app.api.v1.endpoints.errors.logger") as mock_logger:
            response = client.post("/api/v1/errors", json=error_data)

            assert response.status_code == 200
            call_kwargs = mock_logger.error.call_args[1]
            extra = call_kwargs.get("extra", {})
            assert extra.get("has_stack") is True

    def test_log_frontend_error_no_stack(self, client: TestClient):
        """Test that absence of stack trace is logged correctly."""
        error_data = make_error_data()

        with patch("app.api.v1.endpoints.errors.logger") as mock_logger:
            response = client.post("/api/v1/errors", json=error_data)

            assert response.status_code == 200
            call_kwargs = mock_logger.error.call_args[1]
            extra = call_kwargs.get("extra", {})
            assert extra.get("has_stack") is False


class TestErrorsRouterConfiguration:
    """Tests for errors router configuration."""

    def test_router_exists(self):
        """Test that errors router is importable."""
        from app.api.v1.endpoints.errors import router

        assert router is not None

    def test_router_has_correct_tags(self):
        """Test that router has correct tags."""
        from app.api.v1.endpoints.errors import router

        assert "errors" in router.tags

    def test_logger_exists(self):
        """Test that logger is configured."""
        from app.api.v1.endpoints.errors import logger

        assert logger is not None


class TestErrorTypesValidation:
    """Tests for error type validation."""

    def test_valid_error_type_error(self, client: TestClient):
        """Test 'error' type is accepted."""
        error_data = make_error_data(type="error")

        with patch("app.api.v1.endpoints.errors.logger"):
            response = client.post("/api/v1/errors", json=error_data)
            assert response.status_code == 200

    def test_valid_error_type_unhandled_rejection(self, client: TestClient):
        """Test 'unhandledRejection' type is accepted."""
        error_data = make_error_data(type="unhandledRejection")

        with patch("app.api.v1.endpoints.errors.logger"):
            response = client.post("/api/v1/errors", json=error_data)
            assert response.status_code == 200

    def test_valid_error_type_vue_error(self, client: TestClient):
        """Test 'vueError' type is accepted."""
        error_data = make_error_data(type="vueError")

        with patch("app.api.v1.endpoints.errors.logger"):
            response = client.post("/api/v1/errors", json=error_data)
            assert response.status_code == 200

    def test_valid_error_type_manual(self, client: TestClient):
        """Test 'manual' type is accepted."""
        error_data = make_error_data(type="manual")

        with patch("app.api.v1.endpoints.errors.logger"):
            response = client.post("/api/v1/errors", json=error_data)
            assert response.status_code == 200

    def test_invalid_error_type_rejected(self, client: TestClient):
        """Test invalid error type is rejected."""
        error_data = make_error_data(type="invalid-type")

        response = client.post("/api/v1/errors", json=error_data)
        assert response.status_code == 422
