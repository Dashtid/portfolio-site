"""
Best-effort IP-to-country lookup for analytics.

Uses ipapi.co's keyless HTTPS endpoint (1000 lookups/day on the free tier,
well under our traffic). Results are cached in-process for 24h so repeat
visits from the same IP don't re-call upstream. Failures (timeout, rate
limit, network) return None — country stays NULL on the PageView row.

Privacy (D3-BE-03 / SEC-005B): the visitor IP is truncated BEFORE it goes
upstream — IPv4 keeps the /24, IPv6 the /48 — so ipapi.co never sees a
full address it could correlate. Country resolution is unaffected: geo
databases assign country at coarser granularity than these prefixes. The
stored PageView row was already pseudonymised (keyed SHA-256 in
app/utils/ip_hash.py); the third-party disclosure was the remaining raw-IP
sink. Only the ISO-3166 alpha-2 country code comes back.
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


def _truncate_ip(ip: str) -> str | None:
    """Zero the host bits so the upstream lookup never sees a full address.

    IPv4 keeps the /24 (last octet zeroed), IPv6 the /48 (last 80 bits
    zeroed — a /48 is one site under standard allocation, coarser than a
    single subscriber). Returns None for unparseable input.
    """
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return None
    prefix = 24 if addr.version == 4 else 48
    return str(ipaddress.ip_network(f"{addr}/{prefix}", strict=False).network_address)


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
    - The address is truncated (IPv4 /24, IPv6 /48) before the upstream
      call AND before caching — the full IP never leaves this function.
    - Successful and failed lookups are both cached for 24h; keying the
      cache on the truncated address also collapses visitors sharing a
      /24 into one upstream lookup.
    - Any exception (timeout, network, non-2xx, malformed body) returns None.
    """
    lookup_ip = _truncate_ip(ip) if ip and not _is_private_or_local(ip) else None
    if lookup_ip is None:
        return None

    hit, cached = _cache_get(lookup_ip)
    if hit:
        return cached

    try:
        async with httpx.AsyncClient(timeout=LOOKUP_TIMEOUT_SECONDS) as client:
            resp = await client.get(UPSTREAM_URL_TEMPLATE.format(ip=lookup_ip))
        if resp.status_code != 200:
            logger.debug("geo-ip lookup non-200 for %s: %s", lookup_ip, resp.status_code)
            _cache_put(lookup_ip, None)
            return None
        body = resp.text.strip().upper()
        # ipapi.co returns a 2-letter code like "SE". Anything else is junk.
        if len(body) == 2 and body.isalpha():
            _cache_put(lookup_ip, body)
            return body
        logger.debug("geo-ip lookup unexpected body for %s: %r", lookup_ip, body[:40])
        _cache_put(lookup_ip, None)
        return None
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        logger.debug("geo-ip lookup error for %s: %s", lookup_ip, exc)
        _cache_put(lookup_ip, None)
        return None


def _reset_cache_for_tests() -> None:
    """Clear the in-process cache. Call from tests; not part of public API."""
    _cache.clear()
