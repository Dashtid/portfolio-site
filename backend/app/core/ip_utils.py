"""
Shared IP address utilities for security-sensitive operations.

Provides consistent IP extraction across the application, preventing
IP spoofing attacks by only trusting X-Forwarded-For from known proxies.
"""

import ipaddress

from starlette.requests import Request

# Trusted proxy networks (localhost and common private ranges)
# Only IPs from these networks are allowed to set X-Forwarded-For header.
# fc00::/7 covers Fly's private 6PN addresses (fdaa:...) — fly-proxy
# reaches the app over IPv6, so without it every request's direct IP
# looks untrusted and all clients collapse into the proxy's bucket.
TRUSTED_PROXIES = [
    ipaddress.ip_network("127.0.0.0/8"),  # localhost
    ipaddress.ip_network("10.0.0.0/8"),  # private
    ipaddress.ip_network("172.16.0.0/12"),  # private
    ipaddress.ip_network("192.168.0.0/16"),  # private
    ipaddress.ip_network("::1/128"),  # IPv6 localhost
    ipaddress.ip_network("fc00::/7"),  # IPv6 unique-local (Fly 6PN)
]


def is_trusted_proxy(ip_str: str) -> bool:
    """Check if an IP address is from a trusted proxy network."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in network for network in TRUSTED_PROXIES)
    except ValueError:
        return False


def _parse_ip(ip_str: str) -> str | None:
    """Return the normalized IP string, or None if it doesn't parse."""
    try:
        return str(ipaddress.ip_address(ip_str))
    except ValueError:
        return None


def get_client_ip(request: Request) -> str:
    """
    Get the real client IP, only trusting proxy headers from known proxies.

    This prevents IP spoofing attacks where malicious clients send fake
    forwarding headers to bypass IP-based rate limiting or analytics.

    Behind Fly's proxy the authoritative source is Fly-Client-IP, which
    the edge sets itself and clients cannot forge through it. As a
    fallback, X-Forwarded-For is walked RIGHT to LEFT: rightmost entries
    are appended by our own proxies, and the first address not in the
    trusted set is the real client. The leftmost entry is entirely
    client-controlled — trusting it (as this function previously did)
    let any caller choose their own rate-limit bucket.

    Args:
        request: The incoming HTTP request

    Returns:
        Client IP address string, or "unknown" if unavailable
    """
    # Get the direct connection IP
    direct_ip = request.client.host if request.client else None

    # Only consult forwarding headers if the direct connection is trusted
    if direct_ip and is_trusted_proxy(direct_ip):
        fly_ip = request.headers.get("Fly-Client-IP")
        if fly_ip:
            parsed = _parse_ip(fly_ip.strip())
            if parsed:
                return parsed

        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            entries = [part.strip() for part in forwarded.split(",") if part.strip()]
            for entry in reversed(entries):
                parsed = _parse_ip(entry)
                if parsed is None:
                    # Garbage in the chain — stop rather than guess.
                    break
                if not is_trusted_proxy(parsed):
                    return parsed

    return direct_ip or "unknown"
