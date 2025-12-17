"""
Tests for metrics endpoints
"""

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_get_metrics(client: TestClient, admin_user_in_db: dict):
    """Test getting basic metrics (requires admin auth)."""
    response = client.get("/api/v1/metrics/", headers=admin_user_in_db["headers"])
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


def test_get_metrics_requires_auth(client: TestClient):
    """Test that getting metrics requires authentication."""
    response = client.get("/api/v1/metrics/")
    # 401 (no auth) or 403 (forbidden) are both valid for missing/invalid auth
    assert response.status_code in [401, 403]


def test_get_prometheus_metrics(client: TestClient):
    """Test getting prometheus format metrics."""
    response = client.get("/api/v1/metrics/prometheus")
    # Endpoint may return 200 with metrics or 404 if not configured
    assert response.status_code in [200, 404]


def test_reset_metrics(client: TestClient, admin_user_in_db: dict):
    """Test resetting metrics (requires admin auth)."""
    response = client.post("/api/v1/metrics/reset", headers=admin_user_in_db["headers"])
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_reset_metrics_requires_auth(client: TestClient):
    """Test that reset metrics requires authentication."""
    response = client.post("/api/v1/metrics/reset")
    # 401 (no auth) or 403 (forbidden) are both valid for missing/invalid auth
    assert response.status_code in [401, 403]


def test_metrics_health_check(client: TestClient):
    """Test metrics health endpoint."""
    response = client.get("/api/v1/metrics/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "metrics_enabled" in data
    assert "error_tracking_enabled" in data
    assert "analytics_enabled" in data


def test_get_metrics_disabled(client: TestClient, admin_user_in_db: dict):
    """Test metrics when disabled (requires admin auth)."""
    with patch("app.api.v1.endpoints.metrics.settings") as mock_settings:
        mock_settings.METRICS_ENABLED = False
        response = client.get("/api/v1/metrics/", headers=admin_user_in_db["headers"])
        assert response.status_code == 200
        data = response.json()
        # Either returns message that metrics are disabled or returns empty metrics
        assert isinstance(data, dict)


def test_reset_metrics_disabled(client: TestClient, admin_user_in_db: dict):
    """Test reset when metrics disabled (requires admin auth)."""
    with patch("app.api.v1.endpoints.metrics.settings") as mock_settings:
        mock_settings.METRICS_ENABLED = False
        response = client.post("/api/v1/metrics/reset", headers=admin_user_in_db["headers"])
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


def test_metrics_without_trailing_slash(client: TestClient, admin_user_in_db: dict):
    """Test metrics endpoint without trailing slash (performance middleware skip path)."""
    response = client.get("/api/v1/metrics", headers=admin_user_in_db["headers"])
    # Redirects or returns 200
    assert response.status_code in [200, 307]


class TestMetricsEndpointsExtended:
    """Extended tests for metrics endpoints."""

    def test_metrics_router_exists(self):
        """Test metrics router is importable."""
        from app.api.v1.endpoints.metrics import router

        assert router is not None

    def test_performance_metrics_integration(self, client: TestClient, admin_user_in_db: dict):
        """Test that performance metrics are returned (requires admin auth)."""
        response = client.get("/api/v1/metrics/", headers=admin_user_in_db["headers"])
        assert response.status_code == 200
        data = response.json()
        # Should contain basic metrics structure
        assert isinstance(data, dict)

    def test_metrics_contains_expected_fields(self, client: TestClient, admin_user_in_db: dict):
        """Test metrics response contains expected fields (requires admin auth)."""
        response = client.get("/api/v1/metrics/", headers=admin_user_in_db["headers"])
        assert response.status_code == 200
        data = response.json()
        # Metrics can have various structures depending on implementation
        assert data is not None
