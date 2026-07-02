"""
Tests for IP address extraction utilities.

These tests verify the security-focused IP extraction that prevents
IP spoofing attacks by only trusting X-Forwarded-For from known proxies.
"""

from unittest.mock import MagicMock

from starlette.requests import Request

from app.core.ip_utils import get_client_ip, is_trusted_proxy


class TestIsTrustedProxy:
    """Tests for is_trusted_proxy function."""

    def test_localhost_ipv4_trusted(self):
        """127.0.0.1 should be trusted."""
        assert is_trusted_proxy("127.0.0.1") is True

    def test_localhost_range_trusted(self):
        """127.x.x.x range should be trusted."""
        assert is_trusted_proxy("127.0.0.2") is True
        assert is_trusted_proxy("127.255.255.255") is True

    def test_localhost_ipv6_trusted(self):
        """::1 (IPv6 localhost) should be trusted."""
        assert is_trusted_proxy("::1") is True

    def test_private_10_range_trusted(self):
        """10.0.0.0/8 private range should be trusted."""
        assert is_trusted_proxy("10.0.0.1") is True
        assert is_trusted_proxy("10.255.255.255") is True

    def test_private_172_range_trusted(self):
        """172.16.0.0/12 private range should be trusted."""
        assert is_trusted_proxy("172.16.0.1") is True
        assert is_trusted_proxy("172.31.255.255") is True
        # 172.15.x.x is NOT in the range
        assert is_trusted_proxy("172.15.0.1") is False
        # 172.32.x.x is NOT in the range
        assert is_trusted_proxy("172.32.0.1") is False

    def test_private_192_range_trusted(self):
        """192.168.0.0/16 private range should be trusted."""
        assert is_trusted_proxy("192.168.0.1") is True
        assert is_trusted_proxy("192.168.255.255") is True

    def test_public_ips_not_trusted(self):
        """Public IP addresses should NOT be trusted."""
        assert is_trusted_proxy("8.8.8.8") is False
        assert is_trusted_proxy("1.1.1.1") is False
        assert is_trusted_proxy("93.184.216.34") is False
        assert is_trusted_proxy("203.0.113.1") is False

    def test_invalid_ip_not_trusted(self):
        """Invalid IP strings should NOT be trusted."""
        assert is_trusted_proxy("invalid") is False
        assert is_trusted_proxy("") is False
        assert is_trusted_proxy("256.256.256.256") is False
        assert is_trusted_proxy("not-an-ip") is False


class TestGetClientIp:
    """Tests for get_client_ip function."""

    def _create_mock_request(
        self,
        client_host: str | None = None,
        forwarded_for: str | None = None,
    ) -> MagicMock:
        """Create a mock request with specified properties."""
        mock_request = MagicMock(spec=Request)

        if client_host:
            mock_request.client = MagicMock()
            mock_request.client.host = client_host
        else:
            mock_request.client = None

        mock_request.headers = {}
        if forwarded_for:
            mock_request.headers["X-Forwarded-For"] = forwarded_for

        return mock_request

    def test_direct_connection_public_ip(self):
        """Direct connection from public IP returns that IP."""
        mock_request = self._create_mock_request(client_host="93.184.216.34")
        assert get_client_ip(mock_request) == "93.184.216.34"

    def test_direct_connection_no_client(self):
        """No client info returns 'unknown'."""
        mock_request = self._create_mock_request(client_host=None)
        assert get_client_ip(mock_request) == "unknown"

    def test_forwarded_header_ignored_from_public_ip(self):
        """X-Forwarded-For should be IGNORED when connection is from public IP."""
        # Attacker sends fake X-Forwarded-For from their public IP
        mock_request = self._create_mock_request(
            client_host="93.184.216.34",  # Public IP (attacker)
            forwarded_for="1.2.3.4",  # Fake header (should be ignored)
        )
        # Should return the direct IP, NOT the spoofed header
        assert get_client_ip(mock_request) == "93.184.216.34"

    def test_forwarded_header_trusted_from_localhost(self):
        """X-Forwarded-For IS consulted when connection is from localhost.

        The chain is walked right-to-left: rightmost entries are appended
        by our own proxies, so the first untrusted address from the right
        (5.6.7.8) is what the proxy actually saw. The leftmost entry is a
        client-supplied claim and must not win.
        """
        mock_request = self._create_mock_request(
            client_host="127.0.0.1",  # Localhost (trusted proxy)
            forwarded_for="1.2.3.4, 5.6.7.8",  # claimed-by-client, seen-by-proxy
        )
        assert get_client_ip(mock_request) == "5.6.7.8"

    def test_forwarded_header_trusted_from_private_10(self):
        """X-Forwarded-For IS trusted when connection is from 10.x.x.x."""
        mock_request = self._create_mock_request(
            client_host="10.0.0.1",  # Private network (trusted proxy)
            forwarded_for="203.0.113.50",
        )
        assert get_client_ip(mock_request) == "203.0.113.50"

    def test_forwarded_header_trusted_from_private_172(self):
        """X-Forwarded-For IS trusted when connection is from 172.16.x.x."""
        mock_request = self._create_mock_request(
            client_host="172.16.0.1",
            forwarded_for="198.51.100.25",
        )
        assert get_client_ip(mock_request) == "198.51.100.25"

    def test_forwarded_header_trusted_from_private_192(self):
        """X-Forwarded-For IS trusted when connection is from 192.168.x.x."""
        mock_request = self._create_mock_request(
            client_host="192.168.1.1",
            forwarded_for="100.64.0.1",
        )
        assert get_client_ip(mock_request) == "100.64.0.1"

    def test_forwarded_header_skips_trusted_proxies_from_right(self):
        """Trusted proxy hops on the right are skipped to find the client."""
        mock_request = self._create_mock_request(
            client_host="127.0.0.1",  # Trusted proxy
            forwarded_for="1.2.3.4, 10.0.0.1, 192.168.1.1",  # Client + proxies
        )
        assert get_client_ip(mock_request) == "1.2.3.4"

    def test_forwarded_header_with_whitespace(self):
        """Whitespace in X-Forwarded-For is handled correctly."""
        mock_request = self._create_mock_request(
            client_host="127.0.0.1",
            forwarded_for="  1.2.3.4  ,  5.6.7.8  ",
        )
        # Right-to-left: 5.6.7.8 is the first untrusted entry from the right.
        assert get_client_ip(mock_request) == "5.6.7.8"

    def test_fly_client_ip_preferred_over_forwarded(self):
        """Fly-Client-IP (set by the Fly edge itself) wins over XFF."""
        mock_request = self._create_mock_request(
            client_host="172.16.1.114",  # fly-proxy
            forwarded_for="8.8.8.8, 203.0.113.50",
        )
        mock_request.headers["Fly-Client-IP"] = "203.0.113.50"
        assert get_client_ip(mock_request) == "203.0.113.50"

    def test_fly_6pn_ipv6_direct_connection_is_trusted(self):
        """Fly's private 6PN (fdaa:...) direct IPs count as trusted proxies."""
        mock_request = self._create_mock_request(
            client_host="fdaa:31:d8db:a7b:5ba:de2f:fd51:2",
            forwarded_for="203.0.113.50",
        )
        assert get_client_ip(mock_request) == "203.0.113.50"

    def test_empty_forwarded_header_returns_direct_ip(self):
        """Empty X-Forwarded-For returns the direct connection IP."""
        mock_request = self._create_mock_request(
            client_host="127.0.0.1",
            forwarded_for="",
        )
        assert get_client_ip(mock_request) == "127.0.0.1"

    def test_ipv6_localhost_trusted(self):
        """IPv6 localhost (::1) is trusted for X-Forwarded-For."""
        mock_request = self._create_mock_request(
            client_host="::1",
            forwarded_for="2001:db8::1",
        )
        assert get_client_ip(mock_request) == "2001:db8::1"


class TestSecurityScenarios:
    """Security-focused tests for IP spoofing prevention."""

    def _create_mock_request(
        self,
        client_host: str | None = None,
        forwarded_for: str | None = None,
    ) -> MagicMock:
        mock_request = MagicMock(spec=Request)
        if client_host:
            mock_request.client = MagicMock()
            mock_request.client.host = client_host
        else:
            mock_request.client = None
        mock_request.headers = {}
        if forwarded_for:
            mock_request.headers["X-Forwarded-For"] = forwarded_for
        return mock_request

    def test_prevent_rate_limit_bypass(self):
        """
        Attacker cannot bypass rate limiting by spoofing X-Forwarded-For.

        Scenario: Attacker at 93.184.216.34 tries to pretend to be
        different IPs by sending fake X-Forwarded-For headers.
        """
        attacker_ip = "93.184.216.34"  # Attacker's real IP

        # Try various fake IPs
        for fake_ip in ["1.1.1.1", "8.8.8.8", "10.0.0.1", "192.168.1.100"]:
            mock_request = self._create_mock_request(
                client_host=attacker_ip,
                forwarded_for=fake_ip,
            )
            # Should always return attacker's real IP, not the spoofed one
            assert get_client_ip(mock_request) == attacker_ip

    def test_prevent_spoofed_leftmost_entry_behind_proxy(self):
        """
        A client-prepended XFF entry cannot choose the rate-limit bucket.

        Scenario: attacker at 203.0.113.99 connects THROUGH the trusted
        proxy and sends their own X-Forwarded-For: 8.8.8.8. The proxy
        appends the real address, producing "8.8.8.8, 203.0.113.99".
        The old leftmost-first logic returned 8.8.8.8 (attacker-chosen);
        the right-to-left walk returns the address the proxy saw.
        """
        mock_request = self._create_mock_request(
            client_host="172.16.0.1",  # trusted proxy
            forwarded_for="8.8.8.8, 203.0.113.99",
        )
        assert get_client_ip(mock_request) == "203.0.113.99"

    def test_legitimate_proxy_chain(self):
        """
        Legitimate requests through reverse proxy work correctly.

        Scenario: Real user at 203.0.113.50 connects through
        nginx reverse proxy running on 127.0.0.1.
        """
        mock_request = self._create_mock_request(
            client_host="127.0.0.1",  # Nginx on localhost
            forwarded_for="203.0.113.50",  # Real user IP
        )
        # Should return the real user IP
        assert get_client_ip(mock_request) == "203.0.113.50"

    def test_cloud_load_balancer_chain(self):
        """
        Requests through cloud load balancer work correctly.

        Scenario: User connects through AWS/GCP load balancer
        which runs on private network.
        """
        mock_request = self._create_mock_request(
            client_host="10.0.0.50",  # Internal load balancer
            forwarded_for="198.51.100.25, 10.0.0.10",  # User + internal proxy
        )
        # Should return the first (user) IP
        assert get_client_ip(mock_request) == "198.51.100.25"
