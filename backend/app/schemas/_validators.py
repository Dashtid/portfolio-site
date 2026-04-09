"""
Shared Pydantic validators used across schema modules.
"""

import re

# Pattern for safe URLs: http(s)://, relative paths starting with /, or empty
# Blocks javascript:, data:, vbscript: and other XSS vectors
SAFE_URL_PATTERN = re.compile(r"^(https?://|/[^/]|$)")


def validate_safe_url(v: str | None, field_name: str) -> str | None:
    """Validate URL is safe (HTTP(S) or relative path, no XSS vectors)."""
    if v is None or v == "":
        return v
    if not SAFE_URL_PATTERN.match(v):
        raise ValueError(f"{field_name} must be an HTTP(S) URL or relative path starting with /")
    return v
