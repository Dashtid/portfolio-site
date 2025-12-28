"""
Shared IP address utilities for security-sensitive operations.

Provides consistent IP extraction across the application, preventing
IP spoofing attacks by only trusting X-Forwarded-For from known proxies.
"""

import ipaddress

from starlette.requests import Request

# Trusted proxy networks (localhost and common private ranges)
# Only IPs from these networks are allowed to set X-Forwarded-For header
TRUSTED_PROXIES = [
    ipaddress.ip_network("127.0.0.0/8"),  # localhost
    ipaddress.ip_network("10.0.0.0/8"),  # private
    ipaddress.ip_network("172.16.0.0/12"),  # private
    ipaddress.ip_network("192.168.0.0/16"),  # private
    ipaddress.ip_network("::1/128"),  # IPv6 localhost
]


def is_trusted_proxy(ip_str: str) -> bool:
    """Check if an IP address is from a trusted proxy network."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in network for network in TRUSTED_PROXIES)
    except ValueError:
        return False


def get_client_ip(request: Request) -> str:
    """
    Get the real client IP, only trusting X-Forwarded-For from known proxies.

    This prevents IP spoofing attacks where malicious clients send fake
    X-Forwarded-For headers to bypass IP-based rate limiting or analytics.

    Args:
        request: The incoming HTTP request

    Returns:
        Client IP address string, or "unknown" if unavailable
    """
    # Get the direct connection IP
    direct_ip = request.client.host if request.client else None

    # Only trust X-Forwarded-For if the direct connection is from a trusted proxy
    if direct_ip and is_trusted_proxy(direct_ip):
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # X-Forwarded-For can contain multiple IPs: client, proxy1, proxy2
            # The first one is the original client
            client_ip = forwarded.split(",")[0].strip()
            if client_ip:
                return client_ip

    return direct_ip or "unknown"
