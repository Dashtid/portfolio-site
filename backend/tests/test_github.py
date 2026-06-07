"""
Tests for GitHub stats endpoints
"""

from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient


@patch("app.api.v1.github.github_service")
def test_get_github_stats_success(mock_service, client: TestClient):
    """Test successful GitHub stats retrieval."""
    mock_service.get_portfolio_stats = AsyncMock(
        return_value={
            "username": "testuser",
            "public_repos": 25,
            "followers": 50,
            "following": 30,
            "total_stars": 100,
            "total_forks": 10,
            "total_watchers": 20,
            "top_languages": [{"name": "Python", "percentage": 60.0}],
            "featured_repos": [],
        }
    )

    response = client.get("/api/v1/github/stats/testuser")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["public_repos"] == 25


def test_get_github_stats_invalid_username(client: TestClient):
    """Test GitHub stats with invalid username."""
    response = client.get("/api/v1/github/stats/")
    assert response.status_code in [404, 422]


@patch("app.api.v1.github.github_service")
def test_get_github_stats_api_error(mock_service, client: TestClient):
    """Test GitHub stats when API returns error."""
    mock_service.get_portfolio_stats = AsyncMock(side_effect=httpx.RequestError("API Error"))

    response = client.get("/api/v1/github/stats/nonexistentuser")
    assert response.status_code == 500
