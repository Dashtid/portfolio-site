"""
Tests for GitHub stats endpoints
"""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


@patch("app.api.v1.github.github_service")
def test_get_github_stats_success(mock_service, client: TestClient):
    """Test successful GitHub stats retrieval."""
    # Mock the github_service response
    mock_service.get_portfolio_stats = AsyncMock(
        return_value={
            "public_repos": 25,
            "followers": 50,
            "following": 30,
            "total_stars": 100,
            "languages": {"Python": 50, "JavaScript": 30},
        }
    )

    response = client.get("/api/v1/github/stats/testuser")
    assert response.status_code == 200
    data = response.json()
    assert "public_repos" in data
    assert "followers" in data


def test_get_github_stats_invalid_username(client: TestClient):
    """Test GitHub stats with invalid username."""
    response = client.get("/api/v1/github/stats/")
    assert response.status_code in [404, 422]  # Not Found or Unprocessable Entity


@patch("app.api.v1.github.github_service")
def test_get_github_stats_api_error(mock_service, client: TestClient):
    """Test GitHub stats when API returns error."""
    # Mock the service to raise an exception
    mock_service.get_portfolio_stats = AsyncMock(side_effect=Exception("API Error"))

    response = client.get("/api/v1/github/stats/nonexistentuser")
    # Should return 500 as the endpoint catches the exception
    assert response.status_code == 500


@patch("app.api.v1.github.github_service")
def test_get_user_repos(mock_service, client: TestClient):
    """Test getting user repositories."""
    mock_service.get_user_repos = AsyncMock(
        return_value=[
            {
                "name": "test-repo",
                "description": "A test repository",
                "html_url": "https://github.com/testuser/test-repo",
                "stargazers_count": 10,
                "language": "Python",
            }
        ]
    )

    response = client.get("/api/v1/github/repos/testuser")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@patch("app.api.v1.github.github_service")
def test_get_project_stats(mock_service, client: TestClient):
    """Test getting project statistics."""
    mock_service.get_project_stats = AsyncMock(
        return_value={
            "name": "test-repo",
            "description": "A test repository",
            "stargazers_count": 10,
            "forks_count": 5,
            "language": "Python",
        }
    )

    response = client.get("/api/v1/github/project/testuser/test-repo")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data


@patch("app.api.v1.github.github_service")
def test_get_repo_languages(mock_service, client: TestClient):
    """Test getting repository languages."""
    mock_service.get_repo_languages = AsyncMock(
        return_value={"Python": 10000, "JavaScript": 5000, "HTML": 2000}
    )

    response = client.get("/api/v1/github/languages/testuser/test-repo")
    assert response.status_code == 200
    data = response.json()
    assert "languages" in data
    assert "total_bytes" in data


@patch("app.api.v1.github.github_service")
def test_get_repo_languages_error(mock_service, client: TestClient):
    """Test getting repository languages with API error."""
    mock_service.get_repo_languages = AsyncMock(side_effect=Exception("API Error"))

    response = client.get("/api/v1/github/languages/testuser/test-repo")
    assert response.status_code == 500


@patch("app.api.v1.github.github_service")
def test_get_project_stats_error(mock_service, client: TestClient):
    """Test getting project statistics with API error."""
    mock_service.get_project_stats = AsyncMock(side_effect=Exception("API Error"))

    response = client.get("/api/v1/github/project/testuser/test-repo")
    assert response.status_code == 500


@patch("app.api.v1.github.github_service")
def test_get_user_repos_error(mock_service, client: TestClient):
    """Test getting user repositories with API error."""
    mock_service.get_user_repos = AsyncMock(side_effect=Exception("API Error"))

    response = client.get("/api/v1/github/repos/testuser")
    assert response.status_code == 500


@patch("app.api.v1.github.github_service")
def test_get_user_repos_with_limit(mock_service, client: TestClient):
    """Test getting user repositories with limit parameter."""
    mock_service.get_user_repos = AsyncMock(return_value=[{"name": f"repo{i}"} for i in range(10)])

    response = client.get("/api/v1/github/repos/testuser?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5


@patch("app.api.v1.github.github_service")
def test_get_repo_languages_empty(mock_service, client: TestClient):
    """Test getting repository languages when no languages."""
    mock_service.get_repo_languages = AsyncMock(return_value={})

    response = client.get("/api/v1/github/languages/testuser/test-repo")
    assert response.status_code == 200
    data = response.json()
    assert data["total_bytes"] == 0
    assert data["languages"] == []
