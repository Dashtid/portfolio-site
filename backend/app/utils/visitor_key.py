"""
Daily visitor key for page_views.session_id.

daily_visitor_key(ip, user_agent) is "v_" followed by the first 16 hex
characters of HMAC-SHA256(salt, ip + "\\n" + user_agent). The salt is 32
bytes from secrets.token_bytes, held in this module's memory only: it is not
derived from SECRET_KEY, and nothing logs or stores it. One address and
User-Agent pair keeps one key through a UTC day; once the salt is replaced,
no stored value turns a key back into an address.

rotate_daily_salt() draws a new salt when the UTC date differs from the
date of the current one. daily_visitor_key() calls it first, and so does
each cleanup pass in app/main.py, so the previous day's salt is gone within
five minutes of midnight UTC even when no page view arrives.

A restart or a deploy during the day starts a new salt: a visitor seen both
before and after it gets two keys, and counts twice, that day.
"""

import hashlib
import hmac
import secrets
from datetime import UTC, date, datetime

_KEY_PREFIX = "v_"
_KEY_HEX_CHARS = 16
_SALT_BYTES = 32

# The current salt and the UTC date it was drawn for.
_salt_day: date | None = None
_salt: bytes = b""


def _utc_today() -> date:
    return datetime.now(UTC).date()


def rotate_daily_salt() -> None:
    """Draw a new salt when the UTC date differs from the current salt's date."""
    global _salt_day, _salt  # noqa: PLW0603
    today = _utc_today()
    if _salt_day != today:
        _salt = secrets.token_bytes(_SALT_BYTES)
        _salt_day = today


def daily_visitor_key(ip: str, user_agent: str) -> str:
    """The visitor key of one address and User-Agent on the current UTC day."""
    rotate_daily_salt()
    message = ip.encode("utf-8", "replace") + b"\n" + user_agent.encode("utf-8", "replace")
    return _KEY_PREFIX + hmac.new(_salt, message, hashlib.sha256).hexdigest()[:_KEY_HEX_CHARS]
