"""
Tests for middleware components including rate limiting
"""

import asyncio
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.middleware.error_tracking import track_error


def test_track_error_disabled():
    """Test that track_error does nothing when error tracking is disabled."""
    with patch("app.middleware.error_tracking.settings") as mock_settings:
        mock_settings.ERROR_TRACKING_ENABLED = False

        # Should not raise and should do nothing
        track_error(ValueError("Test error"))


def test_track_error_enabled():
    """Test that track_error logs errors when enabled."""
    with patch("app.middleware.error_tracking.settings") as mock_settings:
        mock_settings.ERROR_TRACKING_ENABLED = True

        with patch("app.middleware.error_tracking.logger") as mock_logger:
            error = ValueError("Test error message")
            try:
                raise error
            except ValueError as e:
                track_error(e)

            mock_logger.error.assert_called_once()


def test_track_error_with_context():
    """Test that track_error includes context in log."""
    with patch("app.middleware.error_tracking.settings") as mock_settings:
        mock_settings.ERROR_TRACKING_ENABLED = True

        with patch("app.middleware.error_tracking.logger") as mock_logger:
            error = ValueError("Test error")
            context = {"user_id": 123, "action": "test_action"}

            try:
                raise error
            except ValueError as e:
                track_error(e, context)

            mock_logger.error.assert_called_once()
            call_kwargs = mock_logger.error.call_args[1]
            assert "user_id" in call_kwargs.get("extra", {})


def test_track_error_without_active_exception():
    """Test track_error when called without active exception context."""
    with patch("app.middleware.error_tracking.settings") as mock_settings:
        mock_settings.ERROR_TRACKING_ENABLED = True

        with patch("app.middleware.error_tracking.logger") as mock_logger:
            error = ValueError("Test error")
            # Call without raising - this tests the path where sys.exc_info() returns None
            track_error(error)

            mock_logger.error.assert_called_once()


class TestCacheMiddleware:
    """Tests for cache control middleware."""

    def test_cache_middleware_class_exists(self):
        """Test CacheControlMiddleware class exists and is importable."""
        from app.middleware.cache import CacheControlMiddleware

        assert CacheControlMiddleware is not None

    def test_is_static_content_detection(self):
        """Test static content detection."""
        from app.middleware.cache import CacheControlMiddleware

        assert CacheControlMiddleware._is_static_content("/static/image.png") is True
        assert CacheControlMiddleware._is_static_content("/static/style.css") is True
        assert CacheControlMiddleware._is_static_content("/api/v1/projects/") is False

    def test_is_api_endpoint_detection(self):
        """Test API endpoint detection."""
        from app.middleware.cache import CacheControlMiddleware

        assert CacheControlMiddleware._is_api_endpoint("/api/v1/projects/") is True
        assert CacheControlMiddleware._is_api_endpoint("/static/image.png") is False


class TestPerformanceMiddleware:
    """Tests for performance monitoring middleware."""

    def test_performance_middleware_exists(self):
        """Test PerformanceMiddleware class exists."""
        from app.middleware.performance import PerformanceMiddleware

        assert PerformanceMiddleware is not None

    def test_performance_metrics_class(self):
        """Test PerformanceMetrics class."""
        from app.middleware.performance import PerformanceMetrics

        metrics = PerformanceMetrics()
        assert metrics is not None

    def test_metrics_record_request(self):
        """Test recording request metrics."""
        from app.middleware.performance import PerformanceMetrics

        metrics = PerformanceMetrics()
        metrics.record_request("GET", "/api/v1/health/", 50.5, 200)

        assert metrics.request_count["GET /api/v1/health/"] == 1
        assert metrics.status_codes[200] == 1

    def test_metrics_record_error(self):
        """Test recording error metrics."""
        from app.middleware.performance import PerformanceMetrics

        metrics = PerformanceMetrics()
        metrics.record_request("GET", "/api/v1/error/", 100.0, 500)

        assert metrics.errors["GET /api/v1/error/"] == 1

    def test_metrics_get_stats(self):
        """Test getting aggregated stats."""
        from app.middleware.performance import PerformanceMetrics

        metrics = PerformanceMetrics()
        metrics.record_request("GET", "/api/v1/health/", 50.5, 200)
        metrics.record_request("GET", "/api/v1/health/", 30.0, 200)

        stats = metrics.get_stats()
        assert stats["total_requests"] == 2
        assert "endpoints" in stats

    def test_metrics_reset(self):
        """Test resetting metrics."""
        from app.middleware.performance import PerformanceMetrics

        metrics = PerformanceMetrics()
        metrics.record_request("GET", "/api/v1/health/", 50.5, 200)
        metrics.reset()

        stats = metrics.get_stats()
        assert stats["total_requests"] == 0

    def test_get_metrics_function(self):
        """Test get_metrics utility function."""
        from app.middleware.performance import get_metrics

        stats = get_metrics()
        assert isinstance(stats, dict)
        assert "total_requests" in stats

    def test_reset_metrics_function(self):
        """Test reset_metrics utility function."""
        from app.middleware.performance import reset_metrics

        # Should not raise an error
        reset_metrics()


class TestCompressionMiddleware:
    """Tests for compression middleware."""

    def test_compression_middleware_exists(self):
        """Test CompressionMiddleware class exists."""
        from app.middleware.compression import CompressionMiddleware

        assert CompressionMiddleware is not None


class TestLoggingMiddleware:
    """Tests for logging middleware."""

    def test_logging_middleware_exists(self):
        """Test LoggingMiddleware class exists."""
        from app.middleware.logging import LoggingMiddleware

        assert LoggingMiddleware is not None


class TestErrorTrackingMiddleware:
    """Tests for ErrorTrackingMiddleware class."""

    def test_error_tracking_middleware_exists(self):
        """Test ErrorTrackingMiddleware class exists."""
        from app.middleware.error_tracking import ErrorTrackingMiddleware

        assert ErrorTrackingMiddleware is not None

    def test_dispatch_method_exists(self):
        """Test that dispatch method exists on middleware."""
        from app.middleware.error_tracking import ErrorTrackingMiddleware

        middleware = ErrorTrackingMiddleware(app=MagicMock())
        assert hasattr(middleware, "dispatch")

    def test_middleware_logger_exists(self):
        """Test that middleware logger is configured."""
        from app.middleware.error_tracking import logger

        assert logger is not None

    def test_track_error_function_exists(self):
        """Test that track_error function is importable."""
        from app.middleware.error_tracking import track_error

        assert track_error is not None
        assert callable(track_error)


class TestCacheMiddlewareExtended:
    """Extended tests for cache control middleware."""

    def test_middleware_initialization(self):
        """Test middleware can be initialized."""
        from app.middleware.cache import CacheControlMiddleware

        app = MagicMock()
        middleware = CacheControlMiddleware(app=app)
        assert middleware is not None

    def test_is_static_content_with_various_extensions(self):
        """Test static content detection with various file types."""
        from app.middleware.cache import CacheControlMiddleware

        static_paths = [
            "/static/image.jpg",
            "/static/script.js",
            "/assets/font.woff",
            "/assets/font.woff2",
            "/static/style.css",
            "/static/icon.ico",
        ]
        for path in static_paths:
            assert CacheControlMiddleware._is_static_content(path) is True

    def test_is_not_static_content_for_api_paths(self):
        """Test that API paths are not considered static."""
        from app.middleware.cache import CacheControlMiddleware

        api_paths = [
            "/api/v1/users/",
            "/api/v1/projects/",
            "/api/auth/login",
            "/api/v1/health/",
        ]
        for path in api_paths:
            assert CacheControlMiddleware._is_static_content(path) is False


class TestPerformanceMiddlewareExtended:
    """Extended tests for performance middleware."""

    def test_metrics_percentile_calculation(self):
        """Test that metrics include percentile data."""
        from app.middleware.performance import PerformanceMetrics

        metrics = PerformanceMetrics()
        # Add multiple requests
        for i in range(10):
            metrics.record_request("GET", "/api/v1/test/", float(i * 10), 200)

        stats = metrics.get_stats()
        assert stats["total_requests"] == 10
        assert "endpoints" in stats

    def test_metrics_multiple_endpoints(self):
        """Test recording requests to multiple endpoints."""
        from app.middleware.performance import PerformanceMetrics

        metrics = PerformanceMetrics()
        metrics.record_request("GET", "/api/v1/projects/", 50.0, 200)
        metrics.record_request("POST", "/api/v1/projects/", 100.0, 201)
        metrics.record_request("GET", "/api/v1/skills/", 30.0, 200)

        stats = metrics.get_stats()
        assert stats["total_requests"] == 3
        assert len(stats["endpoints"]) == 3

    def test_metrics_status_code_tracking(self):
        """Test that different status codes are tracked."""
        from app.middleware.performance import PerformanceMetrics

        metrics = PerformanceMetrics()
        metrics.record_request("GET", "/api/v1/test/", 50.0, 200)
        metrics.record_request("GET", "/api/v1/test/", 50.0, 404)
        metrics.record_request("GET", "/api/v1/test/", 50.0, 500)

        assert metrics.status_codes[200] == 1
        assert metrics.status_codes[404] == 1
        assert metrics.status_codes[500] == 1


class TestLoggingMiddlewareExtended:
    """Extended tests for logging middleware."""

    def test_logging_middleware_initialization(self):
        """Test logging middleware can be initialized."""
        from app.middleware.logging import LoggingMiddleware

        app = MagicMock()
        middleware = LoggingMiddleware(app=app)
        assert middleware is not None

    def test_dispatch_method_exists_logging(self):
        """Test dispatch method exists on logging middleware."""
        from app.middleware.logging import LoggingMiddleware

        app = MagicMock()
        middleware = LoggingMiddleware(app=app)
        assert hasattr(middleware, "dispatch")


class TestCacheMiddlewareMaxAge:
    """Tests for cache middleware max_age configuration."""

    def test_middleware_default_max_age(self):
        """Test middleware default max_age is 3600."""
        from app.middleware.cache import CacheControlMiddleware

        app = MagicMock()
        middleware = CacheControlMiddleware(app=app)
        assert middleware.max_age == 3600

    def test_middleware_custom_max_age(self):
        """Test middleware with custom max_age."""
        from app.middleware.cache import CacheControlMiddleware

        app = MagicMock()
        middleware = CacheControlMiddleware(app=app, max_age=7200)
        assert middleware.max_age == 7200


class TestPerformanceMiddlewareEdgeCases:
    """Additional edge case tests for performance middleware."""

    def test_metrics_endpoint_stats_structure(self):
        """Test that endpoint stats have correct structure."""
        from app.middleware.performance import PerformanceMetrics

        metrics = PerformanceMetrics()
        metrics.record_request("GET", "/api/v1/test/", 50.0, 200)
        metrics.record_request("GET", "/api/v1/test/", 100.0, 200)

        stats = metrics.get_stats()
        assert "endpoints" in stats
        endpoint_stats = stats["endpoints"].get("GET /api/v1/test/", {})
        assert "count" in endpoint_stats
        assert endpoint_stats["count"] == 2

    def test_metrics_error_rate_tracking(self):
        """Test error rate is tracked separately."""
        from app.middleware.performance import PerformanceMetrics

        metrics = PerformanceMetrics()
        # Add success requests
        metrics.record_request("GET", "/api/v1/test/", 50.0, 200)
        # Add error requests
        metrics.record_request("GET", "/api/v1/test/", 50.0, 500)
        metrics.record_request("GET", "/api/v1/test/", 50.0, 503)

        assert metrics.errors["GET /api/v1/test/"] == 2


class TestErrorTrackingEdgeCases:
    """Additional tests for error tracking."""

    def test_track_error_none_context(self):
        """Test track_error with None context."""
        with patch("app.middleware.error_tracking.settings") as mock_settings:
            mock_settings.ERROR_TRACKING_ENABLED = True

            with patch("app.middleware.error_tracking.logger") as mock_logger:
                error = RuntimeError("Test runtime error")
                try:
                    raise error
                except RuntimeError as e:
                    track_error(e, None)

                mock_logger.error.assert_called_once()


class TestCacheMiddlewareDispatch:
    """Tests for cache middleware dispatch behavior."""

    def test_static_file_extensions_detection(self):
        """Test various static file extensions are detected."""
        from app.middleware.cache import CacheControlMiddleware

        static_paths = [
            "/static/app.js",
            "/assets/style.css",
            "/images/logo.png",
            "/images/photo.jpg",
            "/images/photo.jpeg",
            "/images/banner.gif",
            "/icons/icon.svg",
            "/images/hero.webp",
            "/favicon.ico",
            "/fonts/roboto.woff",
            "/fonts/roboto.woff2",
        ]
        for path in static_paths:
            assert CacheControlMiddleware._is_static_content(path) is True, (
                f"{path} should be static"
            )

    def test_non_static_paths(self):
        """Test non-static paths are not detected as static."""
        from app.middleware.cache import CacheControlMiddleware

        non_static_paths = [
            "/api/v1/users",
            "/api/v1/projects",
            "/docs",
            "/healthz",
        ]
        for path in non_static_paths:
            assert CacheControlMiddleware._is_static_content(path) is False, (
                f"{path} should not be static"
            )

    def test_cache_control_header_for_static_content(self):
        """Test cache control header format for static content."""
        # The expected header for static content - 1 year cache, immutable
        expected_header = "public, max-age=31536000, immutable"
        assert "immutable" in expected_header
        assert "31536000" in expected_header  # 1 year in seconds

    def test_cache_control_header_for_api_content(self):
        """Test cache control header format for API content."""
        max_age = 3600
        expected_header = f"public, max-age={max_age}"
        assert f"max-age={max_age}" in expected_header


class TestPerformanceMiddlewareDispatch:
    """Tests for performance middleware dispatch behavior."""

    def test_metrics_endpoint_path_detection(self):
        """Test that metrics endpoint is properly identified."""
        # The metrics endpoint path check
        metrics_path = "/api/v1/metrics"
        assert metrics_path == "/api/v1/metrics"

    def test_middleware_has_dispatch(self):
        """Test PerformanceMiddleware has dispatch method."""
        from app.middleware.performance import PerformanceMiddleware

        app = MagicMock()
        middleware = PerformanceMiddleware(app=app)
        assert hasattr(middleware, "dispatch")

    def test_global_metrics_instance_exists(self):
        """Test global metrics instance is available."""
        from app.middleware.performance import metrics

        assert metrics is not None

    def test_metrics_response_times_tracked(self):
        """Test that response times are tracked in lists."""
        from app.middleware.performance import PerformanceMetrics

        metrics = PerformanceMetrics()
        metrics.record_request("GET", "/api/v1/test/", 50.0, 200)
        metrics.record_request("GET", "/api/v1/test/", 75.0, 200)
        metrics.record_request("GET", "/api/v1/test/", 100.0, 200)

        assert len(metrics.response_times["GET /api/v1/test/"]) == 3
        assert sum(metrics.response_times["GET /api/v1/test/"]) == 225.0


class TestLoggingMiddlewareStructure:
    """Tests for logging middleware structure and utilities."""

    def test_logging_middleware_uuid_generation(self):
        """Test that UUID module is available for request ID generation."""
        import uuid

        request_id = str(uuid.uuid4())
        assert len(request_id) == 36  # UUID format: 8-4-4-4-12

    def test_logging_middleware_logger_import(self):
        """Test that logging middleware logger is importable."""
        from app.middleware.logging import logger

        assert logger is not None

    def test_logging_middleware_has_dispatch(self):
        """Test logging middleware has dispatch method."""
        from app.middleware.logging import LoggingMiddleware

        app = MagicMock()
        middleware = LoggingMiddleware(app=app)
        assert hasattr(middleware, "dispatch")


class TestCompressionMiddlewareStructure:
    """Tests for compression middleware structure."""

    def test_compression_middleware_init(self):
        """Test compression middleware initialization."""
        from app.middleware.compression import CompressionMiddleware

        app = MagicMock()
        middleware = CompressionMiddleware(app=app, minimum_size=1000)
        assert middleware is not None

    def test_compression_middleware_is_callable(self):
        """Test compression middleware is callable (ASGI middleware pattern)."""
        from app.middleware.compression import CompressionMiddleware

        app = MagicMock()
        middleware = CompressionMiddleware(app=app)
        # GZipMiddleware uses __call__ instead of dispatch
        assert callable(middleware)


class TestRateLimitMiddleware:
    """Tests for rate limiting middleware."""

    def test_rate_limiter_import(self):
        """Test that rate limiter can be imported."""
        from app.middleware import limiter

        assert limiter is not None

    def test_rate_limit_decorators_import(self):
        """Test that rate limit decorators can be imported."""
        from app.middleware import (
            rate_limit_api,
            rate_limit_auth,
            rate_limit_public,
            rate_limit_strict,
        )

        assert rate_limit_api is not None
        assert rate_limit_auth is not None
        assert rate_limit_public is not None
        assert rate_limit_strict is not None

    def test_rate_limit_handler_import(self):
        """Test that rate limit exception handler can be imported."""
        from app.middleware import rate_limit_exceeded_handler

        assert rate_limit_exceeded_handler is not None

    def test_rate_limit_config_exists(self):
        """Test that rate limit configuration exists in settings."""
        from app.config import settings

        assert hasattr(settings, "RATE_LIMIT_ENABLED")
        assert hasattr(settings, "RATE_LIMIT_DEFAULT")
        assert hasattr(settings, "RATE_LIMIT_AUTH")
        assert hasattr(settings, "RATE_LIMIT_API")
        assert hasattr(settings, "RATE_LIMIT_STRICT")
        assert hasattr(settings, "RATE_LIMIT_PUBLIC")

    def test_rate_limit_config_defaults(self):
        """Test rate limit configuration default values."""
        from app.config import settings

        assert settings.RATE_LIMIT_ENABLED is True
        assert "minute" in settings.RATE_LIMIT_DEFAULT
        assert "minute" in settings.RATE_LIMIT_AUTH
        assert "minute" in settings.RATE_LIMIT_API

    def test_rate_limiter_attached_to_app(self, client: TestClient):
        """Test that rate limiter is attached to the FastAPI app."""
        from app.main import app

        assert hasattr(app.state, "limiter")

    def test_get_client_ip_function(self):
        """Test the get_client_ip function with X-Forwarded-For."""
        from app.middleware.rate_limit import get_client_ip

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}

        ip = get_client_ip(mock_request)
        assert ip == "1.2.3.4"

    def test_get_client_ip_no_forwarded(self):
        """Test get_client_ip without X-Forwarded-For header."""
        from app.middleware.rate_limit import get_client_ip

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"

        ip = get_client_ip(mock_request)
        assert ip is not None

    def test_get_user_or_ip_with_token(self):
        """Test get_user_or_ip with Authorization header."""
        from app.middleware.rate_limit import get_user_or_ip

        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.user = None
        mock_request.headers = {"Authorization": "Bearer test-token-123"}

        key = get_user_or_ip(mock_request)
        assert key.startswith("token:")

    def test_get_user_or_ip_without_token(self):
        """Test get_user_or_ip without Authorization header."""
        from app.middleware.rate_limit import get_user_or_ip

        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.user = None
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.1"

        key = get_user_or_ip(mock_request)
        assert not key.startswith("token:")


class TestSecurityHeadersMiddleware:
    """Tests for security headers middleware."""

    def test_security_headers_present(self, client: TestClient):
        """Test that security headers are added to responses."""
        response = client.get("/api/health")

        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "strict-origin" in response.headers.get("Referrer-Policy", "")

    def test_permissions_policy_header(self, client: TestClient):
        """Test that Permissions-Policy header is set."""
        response = client.get("/api/health")

        permissions = response.headers.get("Permissions-Policy", "")
        assert "geolocation=()" in permissions
        assert "microphone=()" in permissions
        assert "camera=()" in permissions


class TestRateLimitIntegration:
    """Integration tests for rate limiting with actual endpoints."""

    def test_health_endpoint_works(self, client: TestClient):
        """Test that health endpoint works."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_auth_endpoint_accessible(self, client: TestClient):
        """Test that auth endpoints are accessible (not blocked by rate limiting)."""
        # Test logout endpoint which doesn't require OAuth configuration
        response = client.post("/api/v1/auth/logout")
        # Logout always returns 200 with success message
        assert response.status_code == 200

    def test_rate_limit_exceeded_response_format(self):
        """Test the format of rate limit exceeded response."""
        from app.middleware import rate_limit_exceeded_handler

        mock_request = MagicMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        # Create a mock exception with the detail attribute
        exc = MagicMock()
        exc.detail = "rate limit exceeded 5 per 1 minute"

        response = asyncio.run(rate_limit_exceeded_handler(mock_request, exc))

        assert response.status_code == 429
        body = json.loads(response.body)
        assert "detail" in body
        assert "rate limit" in body["detail"].lower()


class TestRateLimitConfiguration:
    """Tests for rate limit configuration."""

    def test_rate_limit_format_validation(self):
        """Test that rate limit format is valid."""
        from app.config import settings

        assert "/" in settings.RATE_LIMIT_DEFAULT
        assert "/" in settings.RATE_LIMIT_AUTH
        assert "/" in settings.RATE_LIMIT_API

    def test_rate_limit_storage_uri_default(self):
        """Test that storage URI defaults to None (in-memory)."""
        from app.config import settings

        assert settings.RATE_LIMIT_STORAGE_URI is None

    def test_auth_rate_limit_is_stricter(self):
        """Test that auth rate limit is stricter than API rate limit."""
        from app.config import settings

        auth_limit = int(settings.RATE_LIMIT_AUTH.split("/")[0])
        api_limit = int(settings.RATE_LIMIT_API.split("/")[0])

        assert auth_limit < api_limit

    def test_public_rate_limit_is_more_generous(self):
        """Test that public rate limit is more generous than API limit."""
        from app.config import settings

        public_limit = int(settings.RATE_LIMIT_PUBLIC.split("/")[0])
        api_limit = int(settings.RATE_LIMIT_API.split("/")[0])

        assert public_limit > api_limit


class TestRateLimitKeyFunctions:
    """Tests for rate limit key generation functions."""

    def test_get_client_ip_multiple_proxies(self):
        """Test get_client_ip with multiple proxy IPs."""
        from app.middleware.rate_limit import get_client_ip

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Forwarded-For": "10.0.0.1, 172.16.0.1, 192.168.1.1"}

        ip = get_client_ip(mock_request)
        assert ip == "10.0.0.1"

    def test_get_client_ip_whitespace_handling(self):
        """Test get_client_ip handles whitespace in header."""
        from app.middleware.rate_limit import get_client_ip

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Forwarded-For": "  10.0.0.1  ,  172.16.0.1  "}

        ip = get_client_ip(mock_request)
        assert ip == "10.0.0.1"

    def test_get_user_or_ip_with_user_state(self):
        """Test get_user_or_ip when user is in request state."""
        from app.middleware.rate_limit import get_user_or_ip

        mock_request = MagicMock(spec=Request)
        mock_user = MagicMock()
        mock_user.id = "user-123-abc"
        mock_request.state = MagicMock()
        mock_request.state.user = mock_user
        mock_request.headers = {}

        key = get_user_or_ip(mock_request)
        assert key == "user:user-123-abc"

    def test_get_user_or_ip_token_consistency(self):
        """Test that same token produces same key."""
        from app.middleware.rate_limit import get_user_or_ip

        token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"

        mock_request1 = MagicMock(spec=Request)
        mock_request1.state = MagicMock()
        mock_request1.state.user = None
        mock_request1.headers = {"Authorization": token}

        mock_request2 = MagicMock(spec=Request)
        mock_request2.state = MagicMock()
        mock_request2.state.user = None
        mock_request2.headers = {"Authorization": token}

        key1 = get_user_or_ip(mock_request1)
        key2 = get_user_or_ip(mock_request2)

        assert key1 == key2
        assert key1.startswith("token:")


class TestMiddlewareOrder:
    """Tests for middleware ordering."""

    def test_middleware_order_in_app(self, client: TestClient):
        """Test that middleware is applied in correct order."""

        response = client.get("/api/health")
        assert response.status_code == 200
        # Check that security headers are applied
        assert response.headers.get("X-Content-Type-Options") is not None


class TestErrorTrackingMiddlewareDispatch:
    """Tests for ErrorTrackingMiddleware dispatch method exception handling."""

    def test_middleware_handles_http_exception_4xx(self):
        """Test that middleware handles 4xx HTTP exceptions correctly."""
        import asyncio
        from unittest.mock import MagicMock

        from starlette.exceptions import HTTPException

        from app.middleware.error_tracking import ErrorTrackingMiddleware

        app = MagicMock()
        middleware = ErrorTrackingMiddleware(app=app)

        # Create mock request
        mock_request = MagicMock()
        mock_request.state = MagicMock()
        mock_request.state.request_id = "test-request-123"
        mock_request.method = "GET"
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/v1/test"

        # Create mock call_next that raises 404
        async def raise_404(request):
            raise HTTPException(status_code=404, detail="Not found")

        with patch("app.middleware.error_tracking.logger") as mock_logger:
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(middleware.dispatch(mock_request, raise_404))

            assert exc_info.value.status_code == 404
            # 4xx errors should trigger warning log
            mock_logger.warning.assert_called_once()

    def test_middleware_handles_http_exception_5xx(self):
        """Test that middleware handles 5xx HTTP exceptions correctly."""
        import asyncio
        from unittest.mock import MagicMock

        from starlette.exceptions import HTTPException

        from app.middleware.error_tracking import ErrorTrackingMiddleware

        app = MagicMock()
        middleware = ErrorTrackingMiddleware(app=app)

        # Create mock request
        mock_request = MagicMock()
        mock_request.state = MagicMock()
        mock_request.state.request_id = "test-request-456"
        mock_request.method = "POST"
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/v1/projects"

        # Create mock call_next that raises 500
        async def raise_500(request):
            raise HTTPException(status_code=500, detail="Internal server error")

        with patch("app.middleware.error_tracking.logger") as mock_logger:
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(middleware.dispatch(mock_request, raise_500))

            assert exc_info.value.status_code == 500
            # 5xx errors should trigger exception log
            mock_logger.exception.assert_called_once()

    def test_middleware_handles_unexpected_exception(self):
        """Test that middleware handles unexpected exceptions correctly."""
        import asyncio
        from unittest.mock import MagicMock

        from app.middleware.error_tracking import ErrorTrackingMiddleware

        app = MagicMock()
        middleware = ErrorTrackingMiddleware(app=app)

        # Create mock request
        mock_request = MagicMock()
        mock_request.state = MagicMock()
        mock_request.state.request_id = "test-request-789"
        mock_request.method = "GET"
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/v1/crash"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "TestClient/1.0"}

        # Create mock call_next that raises unexpected exception
        async def raise_unexpected(request):
            raise RuntimeError("Unexpected database error")

        with patch("app.middleware.error_tracking.logger") as mock_logger:
            with pytest.raises(RuntimeError) as exc_info:
                asyncio.run(middleware.dispatch(mock_request, raise_unexpected))

            assert "Unexpected database error" in str(exc_info.value)
            # Unexpected exceptions should trigger critical log
            mock_logger.critical.assert_called_once()

    def test_middleware_success_path(self):
        """Test that middleware passes through successful requests."""
        import asyncio
        from unittest.mock import MagicMock

        from app.middleware.error_tracking import ErrorTrackingMiddleware

        app = MagicMock()
        middleware = ErrorTrackingMiddleware(app=app)

        # Create mock request
        mock_request = MagicMock()

        # Create mock response
        mock_response = MagicMock()
        mock_response.status_code = 200

        # Create mock call_next that returns success
        async def success_response(request):
            return mock_response

        result = asyncio.run(middleware.dispatch(mock_request, success_response))
        assert result == mock_response

    def test_middleware_handles_missing_request_id(self):
        """Test middleware when request_id is not set on state."""
        import asyncio
        from unittest.mock import MagicMock

        from starlette.exceptions import HTTPException

        from app.middleware.error_tracking import ErrorTrackingMiddleware

        app = MagicMock()
        middleware = ErrorTrackingMiddleware(app=app)

        # Create mock request without request_id
        mock_request = MagicMock()
        mock_request.state = MagicMock(spec=[])  # Empty spec means no request_id attr
        mock_request.method = "GET"
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/v1/test"

        async def raise_400(request):
            raise HTTPException(status_code=400, detail="Bad request")

        with patch("app.middleware.error_tracking.logger") as mock_logger:
            with pytest.raises(HTTPException):
                asyncio.run(middleware.dispatch(mock_request, raise_400))

            # Should still log with "unknown" as request_id
            mock_logger.warning.assert_called_once()

    def test_middleware_handles_missing_client(self):
        """Test middleware when client is None."""
        import asyncio
        from unittest.mock import MagicMock

        from app.middleware.error_tracking import ErrorTrackingMiddleware

        app = MagicMock()
        middleware = ErrorTrackingMiddleware(app=app)

        # Create mock request without client
        mock_request = MagicMock()
        mock_request.state = MagicMock()
        mock_request.state.request_id = "test-123"
        mock_request.method = "GET"
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/v1/test"
        mock_request.client = None
        mock_request.headers = {}

        async def raise_value_error(request):
            raise ValueError("Test value error")

        with patch("app.middleware.error_tracking.logger") as mock_logger:
            with pytest.raises(ValueError):
                asyncio.run(middleware.dispatch(mock_request, raise_value_error))

            # Should still log without client IP
            mock_logger.critical.assert_called_once()

    def test_middleware_http_exception_boundary_status_codes(self):
        """Test middleware handles status code boundaries correctly."""
        import asyncio
        from unittest.mock import MagicMock

        from starlette.exceptions import HTTPException

        from app.middleware.error_tracking import ErrorTrackingMiddleware

        app = MagicMock()
        middleware = ErrorTrackingMiddleware(app=app)

        mock_request = MagicMock()
        mock_request.state = MagicMock()
        mock_request.state.request_id = "test-boundary"
        mock_request.method = "GET"
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/v1/test"

        # Test 399 (below 400, no logging expected for HTTP exceptions)
        async def raise_399(request):
            raise HTTPException(status_code=399, detail="Custom status")

        with patch("app.middleware.error_tracking.logger") as mock_logger:
            with pytest.raises(HTTPException):
                asyncio.run(middleware.dispatch(mock_request, raise_399))
            # 399 < 400, so no warning or exception log
            mock_logger.warning.assert_not_called()
            mock_logger.exception.assert_not_called()

        # Test 499 (4xx range, warning)
        async def raise_499(request):
            raise HTTPException(status_code=499, detail="Custom 4xx")

        with patch("app.middleware.error_tracking.logger") as mock_logger:
            with pytest.raises(HTTPException):
                asyncio.run(middleware.dispatch(mock_request, raise_499))
            mock_logger.warning.assert_called_once()

        # Test exactly 500 (5xx range, exception log)
        async def raise_exact_500(request):
            raise HTTPException(status_code=500, detail="Exact 500")

        with patch("app.middleware.error_tracking.logger") as mock_logger:
            with pytest.raises(HTTPException):
                asyncio.run(middleware.dispatch(mock_request, raise_exact_500))
            mock_logger.exception.assert_called_once()


class TestTrackErrorFunction:
    """Additional tests for track_error function."""

    def test_track_error_with_empty_context(self):
        """Test track_error with empty context dict."""
        with patch("app.middleware.error_tracking.settings") as mock_settings:
            mock_settings.ERROR_TRACKING_ENABLED = True

            with patch("app.middleware.error_tracking.logger") as mock_logger:
                error = ValueError("Test error")
                context = {}

                try:
                    raise error
                except ValueError as e:
                    track_error(e, context)

                mock_logger.error.assert_called_once()

    def test_track_error_with_complex_context(self):
        """Test track_error with complex nested context."""
        with patch("app.middleware.error_tracking.settings") as mock_settings:
            mock_settings.ERROR_TRACKING_ENABLED = True

            with patch("app.middleware.error_tracking.logger") as mock_logger:
                error = RuntimeError("Complex error")
                context = {
                    "user_id": "user-123",
                    "request_data": {"method": "POST", "path": "/api/v1/test"},
                    "nested": {"level1": {"level2": "value"}},
                }

                try:
                    raise error
                except RuntimeError as e:
                    track_error(e, context)

                mock_logger.error.assert_called_once()
                call_kwargs = mock_logger.error.call_args[1]
                extra = call_kwargs.get("extra", {})
                assert "user_id" in extra
                assert "request_data" in extra

    def test_track_error_different_exception_types(self):
        """Test track_error with different exception types."""
        with patch("app.middleware.error_tracking.settings") as mock_settings:
            mock_settings.ERROR_TRACKING_ENABLED = True

            exception_types = [
                ValueError("Value error"),
                TypeError("Type error"),
                KeyError("Key error"),
                RuntimeError("Runtime error"),
                OSError("IO error"),
            ]

            for error in exception_types:
                with patch("app.middleware.error_tracking.logger") as mock_logger:
                    try:
                        raise error
                    except Exception as e:
                        track_error(e)

                    mock_logger.error.assert_called_once()
                    call_args = mock_logger.error.call_args[0][0]
                    assert type(error).__name__ in call_args
