"""
Tests for health check endpoints
"""

from fastapi.testclient import TestClient


def test_basic_health_check(client: TestClient):
    """Test basic health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["service"] == "portfolio-api"


def test_readiness_check(client: TestClient):
    """Test readiness check endpoint (includes database check)."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "timestamp" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert data["checks"]["database"] == "connected"


def test_liveness_check(client: TestClient):
    """Test liveness check endpoint."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data
    assert "python_version" in data


def test_root_endpoint(client: TestClient):
    """Test root API endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data
    assert data["docs"] == "/api/docs"


class TestHealthEndpointsExtended:
    """Extended tests for health endpoints."""

    def test_health_router_exists(self):
        """Test health router is importable."""
        from app.api.v1.endpoints.health import router

        assert router is not None

    def test_health_check_timestamp_format(self, client: TestClient):
        """Test that timestamp is in ISO format."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        # ISO format ends with Z or has timezone info
        assert "T" in data["timestamp"]

    def test_liveness_has_python_version(self, client: TestClient):
        """Test liveness check includes python version info."""
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        data = response.json()
        assert "python_version" in data
        assert "3." in data["python_version"]  # Python 3.x

    def test_readiness_check_success_structure(self, client: TestClient):
        """Test readiness check response structure when database is connected."""
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data
        assert data["checks"]["database"] == "connected"
