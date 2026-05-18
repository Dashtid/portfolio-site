"""Tests for the keyed IP-hash helper used by analytics pseudonymisation."""

from unittest.mock import patch

from app.utils.ip_hash import hash_ip


def test_hash_ip_is_deterministic() -> None:
    """Same IP -> same hash, so returning visitors collapse to one session."""
    assert hash_ip("203.0.113.5") == hash_ip("203.0.113.5")


def test_hash_ip_is_unique_per_ip() -> None:
    """Different IPs map to different hashes."""
    assert hash_ip("203.0.113.5") != hash_ip("203.0.113.6")


def test_hash_ip_is_fixed_width_hex() -> None:
    """16-char hex digest, matching the column width of ip_address / session_id suffix."""
    digest = hash_ip("203.0.113.5")
    assert len(digest) == 16
    assert all(c in "0123456789abcdef" for c in digest)


def test_hash_ip_depends_on_secret_key() -> None:
    """Rotating SECRET_KEY rotates the IP pseudonymisation — the whole point of keying."""
    with patch("app.utils.ip_hash.settings") as mock_settings:
        mock_settings.SECRET_KEY = "key-one"
        h1 = hash_ip("203.0.113.5")
        mock_settings.SECRET_KEY = "key-two"
        h2 = hash_ip("203.0.113.5")
    assert h1 != h2


def test_hash_ip_handles_ipv6() -> None:
    """IPv6 strings pass through cleanly."""
    digest = hash_ip("2001:db8::1")
    assert len(digest) == 16


def test_hash_ip_resists_naked_sha256_rainbow_lookup() -> None:
    """A salted hash MUST NOT equal the unsalted sha256(ip) — that's the rainbow-table escape."""
    import hashlib

    ip = "203.0.113.5"
    unsalted = hashlib.sha256(ip.encode()).hexdigest()[:16]
    assert hash_ip(ip) != unsalted
