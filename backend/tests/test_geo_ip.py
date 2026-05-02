"""
Tests for app/core/geo_ip.py

The module is best-effort by design — upstream failures return None and the
caller persists None. Tests cover the four behaviours that matter:
- Happy path: 200 + valid 2-letter body → country code returned and cached
- Cache hit: second lookup for same IP doesn't call upstream again
- Failure path: timeout / non-200 / malformed body → None, also cached
- Private IPs short-circuit without any HTTP call
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core import geo_ip


@pytest.fixture(autouse=True)
def _clear_cache():
    """Reset the module-level cache between tests so order doesn't matter."""
    geo_ip._reset_cache_for_tests()
    yield
    geo_ip._reset_cache_for_tests()


def _mock_response(status_code: int, text: str) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    return resp


@pytest.mark.asyncio
async def test_returns_country_code_on_success():
    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.get.return_value = _mock_response(200, "SE\n")
        client_cls.return_value = client

        result = await geo_ip.get_country_code("8.8.8.8")

    assert result == "SE"
    client.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_caches_successful_lookup():
    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.get.return_value = _mock_response(200, "SE")
        client_cls.return_value = client

        first = await geo_ip.get_country_code("8.8.8.8")
        second = await geo_ip.get_country_code("8.8.8.8")

    assert first == "SE"
    assert second == "SE"
    # Second lookup should hit the cache, not the upstream.
    assert client.get.await_count == 1


@pytest.mark.asyncio
async def test_caches_failed_lookup():
    """Repeated lookups for the same failing IP shouldn't hammer upstream."""
    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.get.return_value = _mock_response(429, "Too Many Requests")
        client_cls.return_value = client

        first = await geo_ip.get_country_code("8.8.8.8")
        second = await geo_ip.get_country_code("8.8.8.8")

    assert first is None
    assert second is None
    assert client.get.await_count == 1


@pytest.mark.asyncio
async def test_private_ip_skips_upstream():
    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        result = await geo_ip.get_country_code("10.0.0.1")
        assert result is None
        client_cls.assert_not_called()


@pytest.mark.asyncio
async def test_loopback_ip_skips_upstream():
    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        result = await geo_ip.get_country_code("127.0.0.1")
        assert result is None
        client_cls.assert_not_called()


@pytest.mark.asyncio
async def test_empty_ip_returns_none():
    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        result = await geo_ip.get_country_code("")
        assert result is None
        client_cls.assert_not_called()


@pytest.mark.asyncio
async def test_unparseable_ip_returns_none():
    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        result = await geo_ip.get_country_code("not-an-ip")
        assert result is None
        client_cls.assert_not_called()


@pytest.mark.asyncio
async def test_timeout_returns_none():
    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.get.side_effect = httpx.TimeoutException("slow upstream")
        client_cls.return_value = client

        result = await geo_ip.get_country_code("8.8.8.8")

    assert result is None


@pytest.mark.asyncio
async def test_network_error_returns_none():
    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.get.side_effect = httpx.ConnectError("nope")
        client_cls.return_value = client

        result = await geo_ip.get_country_code("8.8.8.8")

    assert result is None


@pytest.mark.asyncio
async def test_malformed_body_returns_none():
    """ipapi.co returns plaintext like 'SE'. HTML/JSON/long strings are junk."""
    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.get.return_value = _mock_response(200, "<html>error</html>")
        client_cls.return_value = client

        result = await geo_ip.get_country_code("8.8.8.8")

    assert result is None


@pytest.mark.asyncio
async def test_country_code_normalised_to_uppercase():
    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.get.return_value = _mock_response(200, "se")
        client_cls.return_value = client

        result = await geo_ip.get_country_code("8.8.8.8")

    assert result == "SE"
