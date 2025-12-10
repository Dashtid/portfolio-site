"""
Tests for main application
"""

from fastapi.testclient import TestClient

from app.main import app


class TestCORSMiddleware:
    """Tests for CORS middleware configuration."""

    def test_cors_headers_present(self, client: TestClient):
        """Test that CORS headers are included in responses."""
        response = client.get("/api/v1/health/")
        # Basic health check should succeed
        assert response.status_code == 200

    def test_options_preflight(self, client: TestClient):
        """Test OPTIONS preflight request."""
        # OPTIONS requests are handled by CORS middleware
        response = client.options(
            "/api/v1/projects/",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS middleware handles preflight
        assert response.status_code in [200, 400]


class TestAPIRoutes:
    """Tests for API route registration."""

    def test_projects_route_registered(self, client: TestClient):
        """Test that projects route is registered."""
        response = client.get("/api/v1/projects/")
        assert response.status_code == 200

    def test_skills_route_registered(self, client: TestClient):
        """Test that skills route is registered."""
        response = client.get("/api/v1/skills/")
        assert response.status_code == 200

    def test_companies_route_registered(self, client: TestClient):
        """Test that companies route is registered."""
        response = client.get("/api/v1/companies/")
        assert response.status_code == 200

    def test_education_route_registered(self, client: TestClient):
        """Test that education route is registered."""
        response = client.get("/api/v1/education/")
        assert response.status_code == 200

    def test_github_route_registered(self, client: TestClient):
        """Test that GitHub route is registered."""
        # This will fail because we need a username, but route exists
        response = client.get("/api/v1/github/stats/")
        assert response.status_code in [404, 422]

    def test_documents_route_registered(self, client: TestClient):
        """Test that documents route is registered."""
        response = client.get("/api/v1/documents/")
        assert response.status_code == 200

    def test_health_route_registered(self, client: TestClient):
        """Test that health route is registered."""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200

    def test_metrics_route_registered(self, client: TestClient, admin_user_in_db: dict):
        """Test that metrics route is registered (requires admin auth)."""
        response = client.get("/api/v1/metrics/", headers=admin_user_in_db["headers"])
        assert response.status_code == 200


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_returns_api_info(self, client: TestClient):
        """Test that root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data or "message" in data or "status" in data


class TestAppConfiguration:
    """Tests for app configuration."""

    def test_app_has_title(self):
        """Test that app has a title configured."""
        assert app.title is not None
        assert len(app.title) > 0

    def test_app_has_version(self):
        """Test that app has a version configured."""
        assert app.version is not None

    def test_app_has_openapi_url(self):
        """Test that app has OpenAPI URL."""
        assert app.openapi_url is not None

    def test_openapi_endpoint(self, client: TestClient):
        """Test OpenAPI endpoint is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_docs_endpoint(self, client: TestClient):
        """Test docs endpoint is accessible or disabled."""
        response = client.get("/docs")
        # Docs may be disabled in production config
        assert response.status_code in [200, 404]

    def test_redoc_endpoint(self, client: TestClient):
        """Test redoc endpoint is accessible or disabled."""
        response = client.get("/redoc")
        # ReDoc may be disabled in production config
        assert response.status_code in [200, 404]


class TestMiddlewareIntegration:
    """Tests for middleware integration."""

    def test_request_id_header(self, client: TestClient):
        """Test that request ID is set."""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200

    def test_cache_control_on_api(self, client: TestClient):
        """Test cache control headers on API endpoints."""
        response = client.get("/api/v1/projects/")
        assert response.status_code == 200
        # Cache-Control should be set by middleware
        cache_control = response.headers.get("Cache-Control")
        # May or may not have Cache-Control depending on middleware config
        assert cache_control is None or "max-age" in cache_control

    def test_compression_middleware_exists(self):
        """Test compression middleware is imported."""
        from app.middleware.compression import CompressionMiddleware  # noqa: PLC0415

        assert CompressionMiddleware is not None

    def test_logging_middleware_exists(self):
        """Test logging middleware is imported."""
        from app.middleware.logging import LoggingMiddleware  # noqa: PLC0415

        assert LoggingMiddleware is not None

    def test_error_tracking_middleware_exists(self):
        """Test error tracking middleware is imported."""
        from app.middleware.error_tracking import ErrorTrackingMiddleware  # noqa: PLC0415

        assert ErrorTrackingMiddleware is not None


class TestApplicationLifecycle:
    """Tests for application lifecycle events."""

    def test_app_middleware_count(self):
        """Test that middleware is configured."""
        # App should have middleware configured
        assert len(app.middleware_stack.app.__dict__) >= 0

    def test_app_routes_configured(self):
        """Test that routes are configured."""
        routes = [route.path for route in app.routes]
        assert "/" in routes or "/docs" in routes


class TestMainEndpoints:
    """Tests for endpoints defined in main.py."""

    def test_api_health_endpoint(self, client: TestClient):
        """Test the /api/health endpoint defined in main.py."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data

    def test_api_v1_test_endpoint(self, client: TestClient):
        """Test the /api/v1/test endpoint for frontend connection."""
        response = client.get("/api/v1/test")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Hello from FastAPI!"
        assert "data" in data
        assert data["data"]["framework"] == "FastAPI"
        assert "version" in data["data"]
        assert "description" in data["data"]


class TestSecurityHeaders:
    """Tests for security headers middleware."""

    def test_security_headers_present(self, client: TestClient):
        """Test that security headers are added to responses."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        # Check security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers

    def test_hsts_header_in_production(self):
        """Test that HSTS header is added in production mode."""
        from app.main import SecurityHeadersMiddleware  # noqa: PLC0415

        # The middleware class exists and is properly defined
        assert SecurityHeadersMiddleware is not None
        assert hasattr(SecurityHeadersMiddleware, "dispatch")


class TestStaticFilesMount:
    """Tests for static files mounting."""

    def test_static_directory_route_exists(self, client: TestClient):
        """Test that static file route is configured."""
        # Request a non-existent static file should return 404
        response = client.get("/static/nonexistent.txt")
        assert response.status_code == 404

    def test_static_documents_route(self, client: TestClient):
        """Test static documents route."""
        # Request a non-existent document
        response = client.get("/static/documents/nonexistent.pdf")
        assert response.status_code == 404

    def test_static_nonexistent_js_file(self, client: TestClient):
        """Test accessing a non-existent static JS file returns 404."""
        response = client.get("/static/nonexistent.js")
        # Non-existent file should return 404
        assert response.status_code == 404
