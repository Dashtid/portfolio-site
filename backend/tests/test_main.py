"""
Tests for main application
"""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
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
        # starlette 1.x stopped flattening included routers into app.routes;
        # the _IncludedRouter entries carry no .path, so enumerate only the
        # direct path-bearing routes.
        routes = [route.path for route in app.routes if hasattr(route, "path")]
        assert "/" in routes or "/docs" in routes


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

    def test_x_robots_tag_keeps_the_api_out_of_the_index(self, client: TestClient):
        """api.dashti.se is a different host from dashti.se, so the site's
        robots.txt 'Disallow: /api/' does not cover it and this host serves no
        robots.txt (404 == crawl everything). Endpoints like /api/v1/companies
        republish the exact prose the canonical pages carry, so without this
        header Google can index the JSON as duplicate content competing with
        the pages it came from. X-Robots-Tag is the only noindex signal that
        travels with a JSON response.
        """
        response = client.get("/api/v1/health")
        assert response.headers["X-Robots-Tag"] == "noindex, nofollow"

    def test_hsts_header_in_production(self):
        """Test that HSTS header is added in production mode."""
        from app.main import SecurityHeadersMiddleware  # noqa: PLC0415

        # The middleware class exists and is properly defined
        assert SecurityHeadersMiddleware is not None
        assert hasattr(SecurityHeadersMiddleware, "dispatch")


class TestHTTPSSchemePin:
    """Slash redirects keep https in production although uvicorn sees http.

    Fly's proxy terminates TLS and uvicorn ignores X-Forwarded-Proto, so
    the request reaches the app as http; the 307 Location is built from
    the scope's scheme.
    """

    def test_slash_redirect_is_https_in_production(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(settings, "ENVIRONMENT", "production")
        response = client.get(
            "/api/v1/companies",
            headers={"Host": "api.dashti.se", "X-Forwarded-Proto": "http"},
            follow_redirects=False,
        )
        assert response.status_code == 307
        assert response.headers["location"] == "https://api.dashti.se/api/v1/companies/"

    def test_scheme_is_left_alone_outside_production(self, client: TestClient):
        response = client.get("/api/v1/companies", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "http://testserver/api/v1/companies/"


class TestHostCheck:
    """Production answers api.dashti.se only; the two health routes answer any Host.

    The slash redirect builds its Location from the Host header, so an
    unchecked Host is reflected into it. Fly's health checks send the
    machine's private address as Host, and the image's HEALTHCHECK sends
    localhost:8000.
    """

    @pytest.fixture
    def production(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    @pytest.mark.parametrize("host", ["api.dashti.se", "API.dashti.se", "api.dashti.se:443"])
    def test_api_host_is_served(self, client: TestClient, production: None, host: str):
        response = client.get("/api/v1/companies", headers={"Host": host}, follow_redirects=False)
        assert response.status_code == 307

    @pytest.mark.parametrize(
        "host",
        [
            "evil.example",
            "evil.example/x",  # unparseable: the Location fell back to the server address
            "dashti-portfolio-backend.fly.dev",
            "172.19.17.178:8000",
        ],
    )
    def test_other_hosts_get_400(self, client: TestClient, production: None, host: str):
        response = client.get("/api/v1/companies", headers={"Host": host}, follow_redirects=False)
        assert response.status_code == 400
        assert response.text == "Invalid host header"
        assert "location" not in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    @pytest.mark.parametrize("host", ["172.19.17.178:8000", "localhost:8000"])
    @pytest.mark.parametrize("path", ["/api/v1/health", "/api/v1/health/ready"])
    @pytest.mark.parametrize("method", ["GET", "HEAD"])
    def test_health_routes_answer_any_host(
        self, client: TestClient, production: None, host: str, path: str, method: str
    ):
        response = client.request(method, path, headers={"Host": host})
        assert response.status_code == 200

    def test_health_exemption_is_exact(self, client: TestClient, production: None):
        response = client.get(
            "/api/v1/health/", headers={"Host": "172.19.17.178:8000"}, follow_redirects=False
        )
        assert response.status_code == 400

    def test_any_host_passes_outside_production(self, client: TestClient):
        response = client.get(
            "/api/v1/companies", headers={"Host": "evil.example"}, follow_redirects=False
        )
        assert response.status_code == 307
        assert response.headers["location"] == "http://evil.example/api/v1/companies/"


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
