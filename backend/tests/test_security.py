"""
Tests for security utilities (JWT tokens — GitHub-OAuth-only).
"""

from datetime import timedelta

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)


class TestJWTTokens:
    """Tests for JWT token creation and verification."""

    def test_create_access_token(self):
        """Test access token creation."""
        token = create_access_token(subject="user123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        token = create_refresh_token(subject="user123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        token = create_access_token(subject="user123")
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_decode_refresh_token(self):
        """Test decoding a refresh token."""
        token = create_refresh_token(subject="user456")
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "user456"
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        """Test that invalid token returns None."""
        result = decode_token("invalid.token.here")
        assert result is None

    def test_decode_expired_token(self):
        """Test that expired token returns None."""
        token = create_access_token(subject="user123", expires_delta=timedelta(seconds=-1))
        result = decode_token(token)
        assert result is None

    def test_custom_expiry(self):
        """Test token with custom expiry."""
        token = create_access_token(subject="user123", expires_delta=timedelta(hours=2))
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "user123"

    def test_token_subject_types(self):
        """Test that various subject types work."""
        for subject in ["user123", 42, "admin@test.com"]:
            token = create_access_token(subject=subject)
            payload = decode_token(token)
            assert payload is not None
            assert payload["sub"] == str(subject)
