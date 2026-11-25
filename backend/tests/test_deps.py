"""
Tests for dependency injection utilities
"""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

from app.core.deps import get_current_admin_user, get_current_user
from app.models.user import User


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    def _create_mock_request(self):
        """Create a mock request with cookies attribute."""
        mock_request = MagicMock()
        mock_request.cookies = {}
        return mock_request

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test get_current_user with invalid token."""
        mock_request = self._create_mock_request()
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")
        mock_db = AsyncMock()

        with patch("app.core.deps.decode_token", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, credentials, mock_db)

            assert exc_info.value.status_code == 401
            assert "Invalid authentication credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_missing_subject(self):
        """Test get_current_user when token has no subject."""
        mock_request = self._create_mock_request()
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
        mock_db = AsyncMock()

        with patch("app.core.deps.decode_token", return_value={"type": "access"}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, credentials, mock_db)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self):
        """Test get_current_user when user is not in database."""
        mock_request = self._create_mock_request()
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")

        # Mock database session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        with patch("app.core.deps.decode_token", return_value={"sub": "user123", "type": "access"}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, credentials, mock_db)

            assert exc_info.value.status_code == 404
            assert "User not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test get_current_user successfully returns user."""
        mock_request = self._create_mock_request()
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")

        # Create mock user
        mock_user = User(id="user123", username="testuser", github_id=12345)

        # Mock database session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        with patch("app.core.deps.decode_token", return_value={"sub": "user123", "type": "access"}):
            result = await get_current_user(mock_request, credentials, mock_db)

            assert result == mock_user
            assert result.id == "user123"


def _admin_request() -> Request:
    """A request to an admin route, as get_current_admin_user receives it."""
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/admin/sentry-panel",
            "headers": [],
            "query_string": b"",
            "client": ("203.0.113.9", 1234),
        }
    )


class TestGetCurrentAdminUser:
    """Tests for get_current_admin_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_admin_user_not_admin(self):
        """Test get_current_admin_user when user is not admin."""
        mock_user = User(id="user123", username="testuser", is_admin=False)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(_admin_request(), mock_user)

        assert exc_info.value.status_code == 403
        assert "Not enough permissions" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_admin_user_success(self):
        """Test get_current_admin_user returns admin user."""
        mock_user = User(id="admin123", username="admin", github_id="67890", is_admin=True)

        result = await get_current_admin_user(_admin_request(), mock_user)

        assert result == mock_user
        assert result.is_admin is True

    @pytest.mark.asyncio
    async def test_admin_flag_with_another_github_id_is_refused(self):
        """A stored is_admin flag is not enough: the GitHub id must be ADMIN_GITHUB_ID."""
        mock_user = User(id="old123", username="old", github_id="11111", is_admin=True)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(_admin_request(), mock_user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_refused_while_admin_github_id_is_unset(self, monkeypatch):
        """With ADMIN_GITHUB_ID unset nobody is the admin (fail closed)."""
        from app.config import settings  # noqa: PLC0415

        monkeypatch.setattr(settings, "ADMIN_GITHUB_ID", None)
        mock_user = User(id="admin123", username="admin", github_id="67890", is_admin=True)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(_admin_request(), mock_user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_a_refusal_is_a_security_event(self, security_records):
        mock_user = User(id="old123", username="old", github_id="11111", is_admin=True)

        with pytest.raises(HTTPException):
            await get_current_admin_user(_admin_request(), mock_user)

        [record] = security_records
        assert record.levelno == logging.WARNING
        assert record.event == "auth.admin_denied"
        assert record.user_id == "old123"
        assert record.github_id == "11111"
        assert record.path == "/api/v1/admin/sentry-panel"
