"""
Tests for dependency injection utilities
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.deps import get_current_admin_user, get_current_user
from app.models.user import User


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test get_current_user with invalid token."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")
        mock_db = AsyncMock()

        with patch("app.core.deps.decode_token", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials, mock_db)

            assert exc_info.value.status_code == 401
            assert "Invalid authentication credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_missing_subject(self):
        """Test get_current_user when token has no subject."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
        mock_db = AsyncMock()

        with patch("app.core.deps.decode_token", return_value={"type": "access"}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials, mock_db)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self):
        """Test get_current_user when user is not in database."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")

        # Mock database session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        with patch("app.core.deps.decode_token", return_value={"sub": "user123"}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials, mock_db)

            assert exc_info.value.status_code == 404
            assert "User not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test get_current_user successfully returns user."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")

        # Create mock user
        mock_user = User(id="user123", username="testuser", github_id=12345)

        # Mock database session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        with patch("app.core.deps.decode_token", return_value={"sub": "user123"}):
            result = await get_current_user(credentials, mock_db)

            assert result == mock_user
            assert result.id == "user123"


class TestGetCurrentAdminUser:
    """Tests for get_current_admin_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_admin_user_not_admin(self):
        """Test get_current_admin_user when user is not admin."""
        mock_user = User(id="user123", username="testuser", is_admin=False)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(mock_user)

        assert exc_info.value.status_code == 403
        assert "Not enough permissions" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_admin_user_success(self):
        """Test get_current_admin_user returns admin user."""
        mock_user = User(id="admin123", username="admin", is_admin=True)

        result = await get_current_admin_user(mock_user)

        assert result == mock_user
        assert result.is_admin is True
