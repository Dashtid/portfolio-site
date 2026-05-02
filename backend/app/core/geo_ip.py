"""
Best-effort IP-to-country lookup for analytics.

Uses ipapi.co's keyless HTTPS endpoint (1000 lookups/day on the free tier,
well under our traffic). Results are cached in-process for 24h so repeat
visits from the same IP don't re-call upstream. Failures (timeout, rate
limit, network) return None — country stays NULL on the PageView row.

Privacy: only the ISO-3166 alpha-2 country code is returned. The caller is
responsible for not persisting the raw IP (we already pseudonymise it via
SHA-256 hash before insert).
"""

import ipaddress
import time

import httpx

from app.utils.logger import get_logger

logger = get_logger(__name__)

UPSTREAM_URL_TEMPLATE = "https://ipapi.co/{ip}/country/"
LOOKUP_TIMEOUT_SECONDS = 1.5
CACHE_TTL_SECONDS = 24 * 60 * 60
# Bound the cache so a flood of unique IPs can't blow up memory.
MAX_CACHE_ENTRIES = 10_000

# Cache: ip -> (country_code_or_none, inserted_at_unix)
_cache: dict[str, tuple[str | None, float]] = {}


def _is_private_or_local(ip: str) -> bool:
    """True for loopback/private/link-local/unspecified addresses."""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True  # treat anything unparseable as not-lookuppable
    return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_unspecified


def _cache_get(ip: str) -> tuple[bool, str | None]:
    """Return (hit, value). value may be None even on a cache hit
    when the upstream previously failed for this IP."""
    entry = _cache.get(ip)
    if entry is None:
        return False, None
    value, inserted_at = entry
    if time.monotonic() - inserted_at > CACHE_TTL_SECONDS:
        _cache.pop(ip, None)
        return False, None
    return True, value


def _cache_put(ip: str, value: str | None) -> None:
    if len(_cache) >= MAX_CACHE_ENTRIES:
        # Crude eviction: drop the oldest 10% by insertion time.
        # Sufficient for an analytics endpoint that almost never approaches the cap.
        cutoff = sorted(_cache.items(), key=lambda kv: kv[1][1])[: MAX_CACHE_ENTRIES // 10]
        for k, _ in cutoff:
            _cache.pop(k, None)
    _cache[ip] = (value, time.monotonic())


async def get_country_code(ip: str) -> str | None:
    """
    Resolve an IP to an ISO-3166 alpha-2 country code, or None on failure.

    - Private/loopback IPs short-circuit to None without an upstream call.
    - Successful and failed lookups are both cached for 24h.
    - Any exception (timeout, network, non-2xx, malformed body) returns None.
    """
    if not ip or _is_private_or_local(ip):
        return None

    hit, cached = _cache_get(ip)
    if hit:
        return cached

    try:
        async with httpx.AsyncClient(timeout=LOOKUP_TIMEOUT_SECONDS) as client:
            resp = await client.get(UPSTREAM_URL_TEMPLATE.format(ip=ip))
        if resp.status_code != 200:
            logger.debug("geo-ip lookup non-200 for %s: %s", ip, resp.status_code)
            _cache_put(ip, None)
            return None
        body = resp.text.strip().upper()
        # ipapi.co returns a 2-letter code like "SE". Anything else is junk.
        if len(body) == 2 and body.isalpha():
            _cache_put(ip, body)
            return body
        logger.debug("geo-ip lookup unexpected body for %s: %r", ip, body[:40])
        _cache_put(ip, None)
        return None
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        logger.debug("geo-ip lookup error for %s: %s", ip, exc)
        _cache_put(ip, None)
        return None


def _reset_cache_for_tests() -> None:
    """Clear the in-process cache. Call from tests; not part of public API."""
    _cache.clear()
