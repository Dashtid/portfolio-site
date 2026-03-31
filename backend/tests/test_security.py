"""
Tests for security utilities (JWT tokens and password hashing)
"""

from datetime import timedelta

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


class TestPasswordHashing:
    """Tests for password hashing functions using bcrypt directly."""

    def test_hash_password(self):
        """Test that password is hashed correctly."""
        password = "test_password_123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_verify_correct_password(self):
        """Test that correct password is verified."""
        password = "test_password_123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Test that wrong password fails verification."""
        password = "correct_password"
        hashed = get_password_hash(password)

        assert verify_password("wrong_password", hashed) is False

    def test_hash_different_passwords(self):
        """Test that different passwords produce different hashes."""
        hash1 = get_password_hash("password1")
        hash2 = get_password_hash("password2")

        assert hash1 != hash2

    def test_hash_same_password_produces_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should differ due to random salt
        assert hash1 != hash2
        # But both should verify
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


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
