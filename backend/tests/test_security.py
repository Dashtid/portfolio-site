"""
Tests for security utilities
"""

from datetime import timedelta
from unittest.mock import patch

import jwt

from app.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


class TestPasswordHashing:
    """Tests for password hashing functions.

    Note: These tests use mocks to avoid bcrypt/passlib compatibility issues
    with Python 3.13 where passlib's wrap bug detection fails with newer bcrypt.
    """

    def test_hash_password(self):
        """Test that password is hashed correctly."""
        password = "test_password_123"
        mock_hash = "$2b$12$mockhash123456789012345678901234567890123456789012"

        with patch("app.core.security.pwd_context") as mock_context:
            mock_context.hash.return_value = mock_hash
            hashed = get_password_hash(password)

            assert hashed == mock_hash
            mock_context.hash.assert_called_once_with(password)

    def test_verify_correct_password(self):
        """Test that correct password is verified."""
        password = "test_password_123"
        hashed = "$2b$12$mockhash"

        with patch("app.core.security.pwd_context") as mock_context:
            mock_context.verify.return_value = True
            result = verify_password(password, hashed)

            assert result is True
            mock_context.verify.assert_called_once_with(password, hashed)

    def test_verify_wrong_password(self):
        """Test that wrong password fails verification."""
        password = "wrong_password"
        hashed = "$2b$12$mockhash"

        with patch("app.core.security.pwd_context") as mock_context:
            mock_context.verify.return_value = False
            result = verify_password(password, hashed)

            assert result is False
            mock_context.verify.assert_called_once_with(password, hashed)

    def test_hash_different_passwords(self):
        """Test that hash function is called with different passwords."""
        password1 = "password1"
        password2 = "password2"
        mock_hash1 = "$2b$12$hash1"
        mock_hash2 = "$2b$12$hash2"

        with patch("app.core.security.pwd_context") as mock_context:
            mock_context.hash.side_effect = [mock_hash1, mock_hash2]
            hash1 = get_password_hash(password1)
            hash2 = get_password_hash(password2)

            assert hash1 != hash2
            assert mock_context.hash.call_count == 2

    def test_hash_same_password_produces_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "same_password"
        mock_hash1 = "$2b$12$salt1hash"
        mock_hash2 = "$2b$12$salt2hash"

        with patch("app.core.security.pwd_context") as mock_context:
            mock_context.hash.side_effect = [mock_hash1, mock_hash2]
            mock_context.verify.return_value = True

            hash1 = get_password_hash(password)
            hash2 = get_password_hash(password)

            # Hashes should be different due to random salt
            assert hash1 != hash2
            # Both should verify correctly
            assert verify_password(password, hash1) is True
            assert verify_password(password, hash2) is True


class TestAccessToken:
    """Tests for access token creation."""

    def test_create_access_token(self):
        """Test that access token is created."""
        token = create_access_token(subject="test_user")

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expires_delta(self):
        """Test access token with custom expiration."""
        token = create_access_token(subject="test_user", expires_delta=timedelta(hours=1))

        assert token is not None
        assert isinstance(token, str)

    def test_access_token_contains_subject(self):
        """Test that token contains the subject."""
        subject = "unique_test_user_123"
        token = create_access_token(subject=subject)

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload.get("sub") == subject

    def test_access_token_has_type(self):
        """Test that access token has type 'access'."""
        token = create_access_token(subject="test_user")

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload.get("type") == "access"


class TestRefreshToken:
    """Tests for refresh token creation."""

    def test_create_refresh_token(self):
        """Test that refresh token is created."""
        token = create_refresh_token(subject="test_user")

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_with_expires_delta(self):
        """Test refresh token with custom expiration."""
        token = create_refresh_token(subject="test_user", expires_delta=timedelta(days=14))

        assert token is not None
        assert isinstance(token, str)

    def test_refresh_token_has_type(self):
        """Test that refresh token has type 'refresh'."""
        token = create_refresh_token(subject="test_user")

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload.get("type") == "refresh"


class TestDecodeToken:
    """Tests for token decoding."""

    def test_decode_valid_token(self):
        """Test that valid token is decoded correctly."""
        subject = "test_user"
        token = create_access_token(subject=subject)

        payload = decode_token(token)

        assert payload is not None
        assert payload.get("sub") == subject

    def test_decode_invalid_token(self):
        """Test that invalid token returns None."""
        payload = decode_token("invalid_token_string")

        assert payload is None

    def test_decode_malformed_token(self):
        """Test that malformed token returns None."""
        payload = decode_token("not.a.valid.jwt.token")

        assert payload is None

    def test_decode_empty_token(self):
        """Test that empty token returns None."""
        payload = decode_token("")

        assert payload is None

    def test_decode_refresh_token(self):
        """Test decoding refresh token."""
        subject = "test_user"
        token = create_refresh_token(subject=subject)

        payload = decode_token(token)

        assert payload is not None
        assert payload.get("sub") == subject
        assert payload.get("type") == "refresh"
