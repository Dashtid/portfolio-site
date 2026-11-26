"""
Shared Pydantic validators used across schema modules.
"""

import re

# Pattern for safe URLs: http(s)://, relative paths starting with /, or empty.
# Blocks javascript:, data:, vbscript: and other XSS vectors, and the
# protocol-relative prefixes // and /\ that name another host: browsers read
# a backslash in an http(s) URL as a slash, and they drop tabs and newlines
# before parsing, so one of those between the two characters counts too.
SAFE_URL_PATTERN = re.compile(r"^(https?://|/(?![\t\n\r]*[/\\])[^/\\]|$)")


def validate_safe_url(v: str | None, field_name: str) -> str | None:
    """Validate URL is safe (HTTP(S) or relative path, no XSS vectors)."""
    if v is None or v == "":
        return v
    if not SAFE_URL_PATTERN.match(v):
        raise ValueError(f"{field_name} must be an HTTP(S) URL or relative path starting with /")
    return v
