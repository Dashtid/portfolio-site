"""
Best-effort IP-to-country lookup for analytics.

Uses ipapi.co's keyless HTTPS endpoint (1000 lookups/day on the free tier,
well under our traffic). Results are cached in-process until the end of the
UTC day, keyed by the truncated address, so repeat visits from the same
network that day don't re-call upstream. Failures (timeout, rate limit,
network) return None — country stays NULL on the PageView row.

The cache belongs to one UTC day. drop_previous_days() empties it when the
UTC date differs from the date its entries were made on; get_country_code()
calls it before reading the cache and again before caching an answer, and
so does each cleanup pass in app/main.py, so the previous day's entries are
gone within five minutes of midnight UTC even when no lookup arrives. An
answer that arrives on a later UTC date than its lookup began on is returned
but not cached. A restart empties the cache too.

Privacy (D3-BE-03 / SEC-005B): the visitor IP is truncated BEFORE it goes
upstream — IPv4 keeps the /24, IPv6 the /48 — so ipapi.co never sees a
full address it could correlate. Country resolution is unaffected: geo
databases assign country at coarser granularity than these prefixes. The
stored PageView row holds no address and no digest of one, only the daily
visitor key of app/utils/visitor_key.py. Only the ISO-3166 alpha-2 country
code comes back.
"""

import ipaddress
from datetime import UTC, date, datetime

import httpx

from app.utils.logger import get_logger

logger = get_logger(__name__)

UPSTREAM_URL_TEMPLATE = "https://ipapi.co/{ip}/country/"
LOOKUP_TIMEOUT_SECONDS = 1.5
# Bound the cache so a flood of unique IPs can't blow up memory.
MAX_CACHE_ENTRIES = 10_000

# Cache: truncated address -> country code, or None for a failed lookup.
# Every entry comes from a lookup that began and ended on the UTC date in
# _cache_day.
_cache: dict[str, str | None] = {}
_cache_day: date | None = None


def _utc_today() -> date:
    return datetime.now(UTC).date()


def drop_previous_days() -> date:
    """Empty the cache when the UTC date differs from the date of its entries.

    Returns the UTC date the cache belongs to from now on.
    """
    global _cache_day  # noqa: PLW0603
    today = _utc_today()
    if _cache_day != today:
        _cache.clear()
        _cache_day = today
    return today


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


def _cache_put(ip: str, value: str | None, started_on: date) -> None:
    """Cache `value` for `ip` when the lookup ends on the UTC date it began on.

    An answer that arrives after midnight UTC is not cached: the cache then
    belongs to the new date, and the lookup began on the previous one.
    """
    if drop_previous_days() != started_on:
        return
    if len(_cache) >= MAX_CACHE_ENTRIES:
        # Crude eviction: drop the oldest 10%, in insertion order.
        # Sufficient for an analytics endpoint that almost never approaches the cap.
        for k in list(_cache)[: MAX_CACHE_ENTRIES // 10]:
            del _cache[k]
    _cache[ip] = value


async def get_country_code(ip: str) -> str | None:
    """
    Resolve an IP to an ISO-3166 alpha-2 country code, or None on failure.

    - Private/loopback IPs short-circuit to None without an upstream call.
    - The address is truncated (IPv4 /24, IPv6 /48) before the upstream
      call AND before caching — the full IP never leaves this function.
    - Successful and failed lookups are both cached until the end of the
      UTC day (drop_previous_days() runs first); an answer that arrives
      after the UTC date has changed is returned but not cached. Keying the
      cache on the truncated address also collapses visitors sharing a /24
      into one upstream lookup.
    - Any exception (timeout, network, non-2xx, malformed body) returns None.
    """
    lookup_ip = _truncate_ip(ip) if ip and not _is_private_or_local(ip) else None
    if lookup_ip is None:
        return None

    started_on = drop_previous_days()
    if lookup_ip in _cache:
        return _cache[lookup_ip]

    # The debug lines below never name the network: they carry the status
    # code, the body's length or the exception's type, since the body and
    # the exception's text can repeat the address or the request URL.
    try:
        async with httpx.AsyncClient(timeout=LOOKUP_TIMEOUT_SECONDS) as client:
            resp = await client.get(UPSTREAM_URL_TEMPLATE.format(ip=lookup_ip))
        if resp.status_code != 200:
            logger.debug("geo-ip lookup non-200: %s", resp.status_code)
            _cache_put(lookup_ip, None, started_on)
            return None
        body = resp.text.strip().upper()
        # ipapi.co returns a 2-letter code like "SE". Anything else is junk.
        if len(body) == 2 and body.isalpha():
            _cache_put(lookup_ip, body, started_on)
            return body
        logger.debug("geo-ip lookup unexpected body (%d characters)", len(body))
        _cache_put(lookup_ip, None, started_on)
        return None
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        logger.debug("geo-ip lookup error: %s", type(exc).__name__)
        _cache_put(lookup_ip, None, started_on)
        return None


def _reset_cache_for_tests() -> None:
    """Clear the in-process cache and its date. Call from tests; not part of public API."""
    global _cache_day  # noqa: PLW0603
    _cache.clear()
    _cache_day = None
