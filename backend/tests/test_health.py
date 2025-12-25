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
    assert data["service"] == "Portfolio API"
    assert "version" in data
    assert "environment" in data
    assert "uptime_seconds" in data
    assert "uptime_human" in data


def test_readiness_check(client: TestClient):
    """Test readiness check endpoint (includes database check)."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "timestamp" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert data["checks"]["database"]["status"] == "connected"
    assert "latency_ms" in data["checks"]["database"]
    assert "uptime_seconds" in data


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
        assert data["checks"]["database"]["status"] == "connected"
        assert "latency_ms" in data["checks"]["database"]
        assert "service" in data
        assert "version" in data
        assert "uptime_seconds" in data


def test_detailed_health_check(client: TestClient):
    """Test detailed health check endpoint."""
    response = client.get("/api/v1/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "service" in data
    assert data["service"]["name"] == "Portfolio API"
    assert "version" in data["service"]
    assert "environment" in data["service"]
    assert "runtime" in data
    assert "python_version" in data["runtime"]
    assert "uptime_seconds" in data["runtime"]
    assert "uptime_human" in data["runtime"]
    assert "checks" in data
    assert data["checks"]["database"]["status"] == "healthy"
    assert "latency_ms" in data["checks"]["database"]
    assert "response_time_ms" in data


def test_detailed_health_response_time(client: TestClient):
    """Test that detailed health check measures response time."""
    response = client.get("/api/v1/health/detailed")
    assert response.status_code == 200
    data = response.json()
    # Response time should be a positive number
    assert data["response_time_ms"] >= 0
    # Response time should be reasonable (less than 5 seconds)
    assert data["response_time_ms"] < 5000


class TestHealthUptimeFormatting:
    """Tests for uptime formatting."""

    def test_uptime_seconds_is_positive(self, client: TestClient):
        """Test that uptime seconds is a positive number."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["uptime_seconds"] >= 0

    def test_uptime_human_readable_format(self, client: TestClient):
        """Test that uptime_human is in expected format."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        # Should contain at least seconds
        assert "s" in data["uptime_human"]

    def test_liveness_uptime_matches_health(self, client: TestClient):
        """Test that uptime is consistent across endpoints."""
        health_response = client.get("/api/v1/health")
        live_response = client.get("/api/v1/health/live")

        health_uptime = health_response.json()["uptime_seconds"]
        live_uptime = live_response.json()["uptime_seconds"]

        # Uptime should be within 1 second of each other
        assert abs(health_uptime - live_uptime) < 1


class TestHealthDatabaseFailure:
    """Tests for health endpoints when database fails."""

    def test_readiness_returns_503_on_db_failure(self, client: TestClient):
        """Test readiness check returns 503 when database is unavailable."""
        from unittest.mock import AsyncMock

        from app.database import get_db

        # Mock database to raise exception
        async def mock_db_failure():
            mock_session = AsyncMock()
            mock_session.execute.side_effect = Exception("Database connection failed")
            yield mock_session

        from app.main import app

        app.dependency_overrides[get_db] = mock_db_failure

        try:
            response = client.get("/api/v1/health/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "not_ready"
            assert "database" in data["checks"]
            assert data["checks"]["database"]["status"] == "error"
            assert "error" in data["checks"]["database"]
        finally:
            # Restore original dependency
            del app.dependency_overrides[get_db]

    def test_detailed_returns_503_on_db_failure(self, client: TestClient):
        """Test detailed health check returns 503 when database is unavailable."""
        from unittest.mock import AsyncMock

        from app.database import get_db

        # Mock database to raise exception
        async def mock_db_failure():
            mock_session = AsyncMock()
            mock_session.execute.side_effect = Exception("Connection refused")
            yield mock_session

        from app.main import app

        app.dependency_overrides[get_db] = mock_db_failure

        try:
            response = client.get("/api/v1/health/detailed")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["checks"]["database"]["status"] == "unhealthy"
            assert "error" in data["checks"]["database"]
        finally:
            # Restore original dependency
            del app.dependency_overrides[get_db]

    def test_liveness_works_without_database(self, client: TestClient):
        """Test liveness check doesn't require database."""
        from unittest.mock import AsyncMock

        from app.database import get_db

        # Mock database to raise exception
        async def mock_db_failure():
            mock_session = AsyncMock()
            mock_session.execute.side_effect = Exception("Database down")
            yield mock_session

        from app.main import app

        app.dependency_overrides[get_db] = mock_db_failure

        try:
            # Liveness should still return 200 - it doesn't check database
            response = client.get("/api/v1/health/live")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "alive"
        finally:
            # Restore original dependency
            del app.dependency_overrides[get_db]

    def test_basic_health_works_without_database(self, client: TestClient):
        """Test basic health check doesn't require database."""
        from unittest.mock import AsyncMock

        from app.database import get_db

        # Mock database to raise exception
        async def mock_db_failure():
            mock_session = AsyncMock()
            mock_session.execute.side_effect = Exception("Database down")
            yield mock_session

        from app.main import app

        app.dependency_overrides[get_db] = mock_db_failure

        try:
            # Basic health should still return 200 - no database check
            response = client.get("/api/v1/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        finally:
            # Restore original dependency
            del app.dependency_overrides[get_db]
