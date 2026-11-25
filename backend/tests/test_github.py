"""
Tests for GitHub stats endpoints
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient


@patch("app.api.v1.github.github_service")
def test_get_github_stats_success(mock_service, client: TestClient):
    """Test successful GitHub stats retrieval."""
    mock_service.get_portfolio_stats = AsyncMock(
        return_value={
            "username": "Dashtid",
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

    response = client.get("/api/v1/github/stats/Dashtid")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "Dashtid"
    assert data["public_repos"] == 25
    mock_service.get_portfolio_stats.assert_awaited_once_with("Dashtid")


def test_get_github_stats_invalid_username(client: TestClient):
    """Test GitHub stats with invalid username."""
    response = client.get("/api/v1/github/stats/")
    assert response.status_code in [404, 422]


@pytest.mark.parametrize("username", ["octocat", "dashtid", "DASHTID"])
@patch("app.api.v1.github.github_service")
def test_get_github_stats_other_username_is_404(mock_service, username: str, client: TestClient):
    """Only the site owner's account is served; nothing else reaches GitHub.

    Case variants are refused too: each spelling would be its own cache
    key, so serving them would let a caller force an upstream fetch per
    request on the server's token.
    """
    mock_service.get_portfolio_stats = AsyncMock()

    response = client.get(f"/api/v1/github/stats/{username}")
    assert response.status_code == 404
    mock_service.get_portfolio_stats.assert_not_awaited()


@patch("app.api.v1.github.github_service")
def test_get_github_stats_api_error(mock_service, client: TestClient):
    """Test GitHub stats when API returns error."""
    mock_service.get_portfolio_stats = AsyncMock(side_effect=httpx.RequestError("API Error"))

    response = client.get("/api/v1/github/stats/Dashtid")
    assert response.status_code == 500
