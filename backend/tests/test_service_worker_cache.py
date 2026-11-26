"""The service worker's api-cache stores no response of a signed-in route.

Workbox's runtime caching ignores a response's Cache-Control, and what it
stores in CacheStorage outlives the session that fetched it. The service
worker built from frontend/vite.config.ts sends a GET to the api-cache only
when its URL matches the urlPattern of the runtimeCaching entry named
'api-cache'. These tests read that pattern and hold it against every GET
route of this API that needs a signed-in user, taken from the app's own
routing table, so an admin route mounted under a public prefix, as
/skills/admin/all and /education/admin/all are, fails here when it is added.
"""

import re
from pathlib import Path
from urllib.parse import urlsplit

from fastapi.routing import APIRoute

from app.core.deps import get_current_user
from app.main import app

VITE_CONFIG = Path(__file__).resolve().parents[2] / "frontend" / "vite.config.ts"
SITE = "https://dashti.se"
API = "https://api.dashti.se"
SAMPLE_ID = "0b9a43f5-5c2e-4f0e-9d3b-2d8e6c1f7a90"


def _api_cache_pattern() -> re.Pattern[str]:
    """The api-cache urlPattern, a JavaScript regex literal, compiled for Python.

    The pattern uses syntax both engines read alike; a flag other than i
    fails here instead of being dropped.
    """
    config = VITE_CONFIG.read_text(encoding="utf-8")
    head = config[: config.index("cacheName: 'api-cache'")]
    start = head.rindex("urlPattern:") + len("urlPattern:")
    literal = head[start : head.rindex("handler:")].strip().removesuffix(",")
    body, _, flags = literal[1:].rpartition("/")
    assert literal.startswith("/"), literal
    assert body, literal
    assert set(flags) <= {"i"}, flags
    return re.compile(body, re.IGNORECASE if "i" in flags else 0)


def _routed(url: str) -> bool:
    """Whether the service worker of https://dashti.se caches a GET of `url`.

    As workbox-routing's RegExpRoute decides: a match anywhere in the URL,
    which for a cross-origin URL must start at its first character.
    """
    match = _api_cache_pattern().search(url)
    same_origin = urlsplit(url)[:2] == urlsplit(SITE)[:2]
    return match is not None and (same_origin or match.start() == 0)


def _needs_a_signed_in_user(route: APIRoute) -> bool:
    """Whether get_current_user is in the route's dependency tree.

    get_current_admin_user depends on it, so every admin route counts too.
    """
    pending = list(route.dependant.dependencies)
    while pending:
        dependant = pending.pop()
        if dependant.call is get_current_user:
            return True
        pending.extend(dependant.dependencies)
    return False


def _signed_in_reads() -> list[str]:
    """The path of every GET route that needs a signed-in user, ids filled in."""
    return sorted(
        re.sub(r"\{[^}]+\}", SAMPLE_ID, route.path)
        for route in app.routes
        if isinstance(route, APIRoute) and "GET" in route.methods and _needs_a_signed_in_user(route)
    )


def test_the_route_list_holds_the_admin_reads_under_public_prefixes() -> None:
    reads = _signed_in_reads()
    assert {"/api/v1/skills/admin/all", "/api/v1/education/admin/all", "/api/v1/auth/me"} <= set(
        reads
    )
    assert "/api/v1/skills/" not in reads


def test_no_read_that_needs_a_signed_in_user_is_cached() -> None:
    cached = [
        url
        for path in _signed_in_reads()
        for url in (f"{API}{path}", f"{API}{path}?days=30", f"{API}{path.rstrip('/')}/")
        if _routed(url)
    ]
    assert cached == []


def test_the_public_reads_are_still_cached() -> None:
    """The pattern still matches, so the exclusions above are not vacuous."""
    for path in ("/api/v1/skills/", "/api/v1/education/", f"/api/v1/companies/{SAMPLE_ID}"):
        assert _routed(f"{API}{path}"), path
