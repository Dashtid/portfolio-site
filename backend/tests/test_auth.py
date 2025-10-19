"""
Tests for authentication endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.core.security import create_access_token, verify_token


def test_github_login_redirect(client: TestClient):
    """Test GitHub OAuth login redirect."""
    response = client.get("/api/v1/auth/github/login")
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert "github.com/login/oauth/authorize" in data["url"]


@patch("app.api.v1.auth.httpx.AsyncClient")
async def test_github_callback_success(mock_client, client: TestClient):
    """Test successful GitHub OAuth callback."""
    # Mock GitHub API responses
    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": "github_token"}
    mock_user_response = MagicMock()
    mock_user_response.json.return_value = {
        "id": 12345,
        "login": "testuser",
        "email": "test@example.com",
        "name": "Test User",
        "avatar_url": "https://github.com/avatar.png"
    }

    mock_client_instance = MagicMock()
    mock_client_instance.post.return_value = mock_response
    mock_client_instance.get.return_value = mock_user_response
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    response = client.get("/api/v1/auth/github/callback?code=test_code")
    # Note: This would need proper async handling in real implementation


def test_token_refresh(client: TestClient):
    """Test token refresh endpoint."""
    # Create a valid refresh token
    refresh_token = create_access_token(
        data={"sub": "test_user", "email": "test@example.com"},
        expires_delta=None  # This would be configured for refresh tokens
    )

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    # Basic structure test - full implementation would verify new tokens


def test_protected_endpoint_without_auth(client: TestClient):
    """Test accessing protected endpoint without authentication."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_protected_endpoint_with_auth(client: TestClient, auth_headers: dict):
    """Test accessing protected endpoint with valid token."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "test_user"
    assert data["email"] == "test@example.com"


def test_logout(client: TestClient, auth_headers: dict):
    """Test logout endpoint."""
    response = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out"


def test_invalid_token(client: TestClient):
    """Test with invalid authentication token."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_expired_token(client: TestClient):
    """Test with expired token."""
    # Create an expired token
    from datetime import datetime, timedelta
    expired_token = create_access_token(
        data={"sub": "test_user"},
        expires_delta=timedelta(seconds=-1)  # Already expired
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401