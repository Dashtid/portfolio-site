"""
Tests for GitHub stats endpoints
"""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


@patch("app.api.v1.github.httpx.AsyncClient")
def test_get_github_stats_success(mock_client, client: TestClient):
    """Test successful GitHub stats retrieval."""
    # Mock GitHub API responses
    mock_user_response = MagicMock()
    mock_user_response.status_code = 200
    mock_user_response.json.return_value = {"public_repos": 25, "followers": 50, "following": 30}

    mock_repos_response = MagicMock()
    mock_repos_response.status_code = 200
    mock_repos_response.json.return_value = [
        {
            "name": "test-repo",
            "description": "Test repository",
            "html_url": "https://github.com/user/test-repo",
            "stargazers_count": 10,
            "forks_count": 5,
            "language": "Python",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
        }
    ]

    mock_client_instance = MagicMock()
    mock_client_instance.get.side_effect = [mock_user_response, mock_repos_response]
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    response = client.get("/api/v1/github/stats/testuser")
    assert response.status_code == 200
    data = response.json()
    assert "public_repos" in data
    assert "followers" in data


def test_get_github_stats_invalid_username(client: TestClient):
    """Test GitHub stats with invalid username."""
    response = client.get("/api/v1/github/stats/")
    assert response.status_code in [404, 422]  # Not Found or Unprocessable Entity


@patch("app.api.v1.github.httpx.AsyncClient")
def test_get_github_stats_api_error(mock_client, client: TestClient):
    """Test GitHub stats when API returns error."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = Exception("Not Found")

    mock_client_instance = MagicMock()
    mock_client_instance.get.return_value = mock_response
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    response = client.get("/api/v1/github/stats/nonexistentuser")
    # Should handle error gracefully
    assert response.status_code in [404, 500]
