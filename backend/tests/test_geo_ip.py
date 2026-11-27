"""
Tests for app/core/geo_ip.py

The module is best-effort by design — upstream failures return None and the
caller persists None. Tests cover the five behaviours that matter:
- Happy path: 200 + valid 2-letter body → country code returned and cached
- Cache hit: second lookup for same IP doesn't call upstream again
- Failure path: timeout / non-200 / malformed body → None, also cached, and
  a debug line that does not name the network
- Private IPs short-circuit without any HTTP call
- One UTC day: drop_previous_days() empties a cache made on an earlier UTC
  date, when it runs, at the next lookup and at each cleanup pass, and keeps
  the entries of the same day; an answer that arrives on a later UTC date
  than its lookup began on is returned but not cached
"""

import asyncio
import logging
from collections.abc import Callable, Iterator
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core import geo_ip
from tests.conftest import run_one_cleanup_pass

DAY = date(2030, 1, 1)


@pytest.fixture(autouse=True)
def _clear_cache():
    """Reset the module-level cache between tests so order doesn't matter."""
    geo_ip._reset_cache_for_tests()
    yield
    geo_ip._reset_cache_for_tests()


@pytest.fixture
def set_day(monkeypatch: pytest.MonkeyPatch) -> Callable[[date], None]:
    """Start on DAY; the returned setter moves the UTC date the module sees."""
    today = [DAY]
    monkeypatch.setattr(geo_ip, "_utc_today", lambda: today[0])

    def move_to(day: date) -> None:
        today[0] = day

    return move_to


@pytest.fixture
def debug_records() -> Iterator[list[logging.LogRecord]]:
    """Every record the module's logger emits at DEBUG or above during the test."""
    records: list[logging.LogRecord] = []

    class Keep(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    keep = Keep(logging.DEBUG)
    level = geo_ip.logger.level
    geo_ip.logger.addHandler(keep)
    geo_ip.logger.setLevel(logging.DEBUG)
    try:
        yield records
    finally:
        geo_ip.logger.setLevel(level)
        geo_ip.logger.removeHandler(keep)


def _mock_response(status_code: int, text: str) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    return resp


def _upstream_answering(client_cls: MagicMock, text: str = "SE") -> AsyncMock:
    """Make the patched httpx.AsyncClient answer every lookup 200 with `text`."""
    client = AsyncMock()
    client.__aenter__.return_value = client
    client.get.return_value = _mock_response(200, text)
    client_cls.return_value = client
    return client


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


# A body that repeats the network it was asked about, as a JSON error might.
_ECHO_BODY = '{"ip": "8.8.8.0", "error": true}'


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("upstream", "line"),
    [
        (_mock_response(429, "8.8.8.0 is rate limited"), "geo-ip lookup non-200: 429"),
        (
            _mock_response(200, _ECHO_BODY),
            f"geo-ip lookup unexpected body ({len(_ECHO_BODY)} characters)",
        ),
        (
            httpx.TimeoutException("timed out: https://ipapi.co/8.8.8.0/country/"),
            "geo-ip lookup error: TimeoutException",
        ),
    ],
    ids=["non-200", "junk body", "timeout"],
)
async def test_a_failed_lookup_logs_no_network(
    upstream: MagicMock | Exception, line: str, debug_records: list[logging.LogRecord]
):
    """The debug line of each failed lookup, where the answer repeats the network too."""
    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        client = AsyncMock()
        client.__aenter__.return_value = client
        if isinstance(upstream, Exception):
            client.get.side_effect = upstream
        else:
            client.get.return_value = upstream
        client_cls.return_value = client

        assert await geo_ip.get_country_code("8.8.8.8") is None

    assert [record.getMessage() for record in debug_records] == [line]
    for record in debug_records:
        assert "8.8.8" not in record.getMessage()
        assert "8.8.8" not in repr(record.args)


# ---- D3-BE-03: IP truncation before the third-party lookup -----------------


def test_truncate_ipv4_zeroes_last_octet():
    assert geo_ip._truncate_ip("8.8.8.77") == "8.8.8.0"


def test_truncate_ipv6_keeps_the_48():
    assert geo_ip._truncate_ip("2001:db8:abcd:12:34:56:78:9a") == "2001:db8:abcd::"


def test_truncate_unparseable_returns_none():
    assert geo_ip._truncate_ip("not-an-ip") is None


@pytest.mark.asyncio
async def test_upstream_never_sees_the_full_ip():
    """The URL sent to ipapi.co must carry the truncated address only."""
    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.get.return_value = _mock_response(200, "SE")
        client_cls.return_value = client

        result = await geo_ip.get_country_code("8.8.8.77")

    assert result == "SE"
    (called_url,) = client.get.await_args.args
    assert "8.8.8.0" in called_url
    assert "8.8.8.77" not in called_url


@pytest.mark.asyncio
async def test_cache_collapses_a_shared_slash_24():
    """Two visitors in the same /24 should cost one upstream lookup."""
    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.get.return_value = _mock_response(200, "SE")
        client_cls.return_value = client

        first = await geo_ip.get_country_code("8.8.8.10")
        second = await geo_ip.get_country_code("8.8.8.200")

    assert first == "SE"
    assert second == "SE"
    assert client.get.await_count == 1


# ---- The cache holds the lookups of one UTC day ----------------------------


@pytest.mark.asyncio
async def test_drop_previous_days_empties_a_cache_made_on_an_earlier_utc_date(
    set_day: Callable[[date], None],
):
    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        _upstream_answering(client_cls)
        assert await geo_ip.get_country_code("8.8.8.8") == "SE"
    assert geo_ip._cache == {"8.8.8.0": "SE"}

    set_day(DAY + timedelta(days=1))
    geo_ip.drop_previous_days()

    assert geo_ip._cache == {}
    assert geo_ip._cache_day == DAY + timedelta(days=1)


@pytest.mark.asyncio
async def test_the_first_lookup_of_a_new_utc_day_drops_the_previous_days_entries(
    set_day: Callable[[date], None],
):
    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        client = _upstream_answering(client_cls)
        await geo_ip.get_country_code("8.8.8.8")
        await geo_ip.get_country_code("8.8.4.4")
        set_day(DAY + timedelta(days=1))
        assert await geo_ip.get_country_code("8.8.8.8") == "SE"

    # Upstream is asked again, and the other network of the previous day is gone.
    assert client.get.await_count == 3
    assert geo_ip._cache == {"8.8.8.0": "SE"}


@pytest.mark.asyncio
async def test_entries_of_the_same_utc_day_stay(set_day: Callable[[date], None]):
    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        client = _upstream_answering(client_cls)
        await geo_ip.get_country_code("8.8.8.8")
        geo_ip.drop_previous_days()
        assert await geo_ip.get_country_code("8.8.8.8") == "SE"

    assert client.get.await_count == 1
    assert geo_ip._cache == {"8.8.8.0": "SE"}
    assert geo_ip._cache_day == DAY


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "drop_while_waiting", [True, False], ids=["a drop while it waits", "no drop while it waits"]
)
async def test_an_answer_that_arrives_on_a_later_utc_date_is_not_cached(
    set_day: Callable[[date], None], drop_while_waiting: bool
):
    """A lookup that begins before midnight UTC and is answered after it.

    The answer is returned and not cached, whether or not a cleanup pass or
    another lookup moved the cache to the new date while upstream was asked.
    """
    asked = asyncio.Event()
    released = asyncio.Event()

    async def answer_once_released(url: str) -> MagicMock:
        asked.set()
        await released.wait()
        return _mock_response(200, "SE")

    with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
        client = _upstream_answering(client_cls)
        client.get.side_effect = answer_once_released
        lookup = asyncio.create_task(geo_ip.get_country_code("8.8.8.8"))
        await asyncio.wait_for(asked.wait(), timeout=5)
        set_day(DAY + timedelta(days=1))
        if drop_while_waiting:
            geo_ip.drop_previous_days()
        released.set()
        assert await asyncio.wait_for(lookup, timeout=5) == "SE"

    assert geo_ip._cache == {}
    assert geo_ip._cache_day == DAY + timedelta(days=1)


def test_a_cleanup_pass_drops_the_entries_of_a_past_day(
    client: TestClient, set_day: Callable[[date], None]
):
    """The entries go at the first cleanup pass of a new UTC day, lookup or not."""
    _ = client  # the pass deletes from tables the fixture creates

    async def look_up() -> str | None:
        with patch("app.core.geo_ip.httpx.AsyncClient") as client_cls:
            _upstream_answering(client_cls)
            return await geo_ip.get_country_code("8.8.8.8")

    assert asyncio.run(look_up()) == "SE"
    set_day(DAY + timedelta(days=1))

    asyncio.run(run_one_cleanup_pass())

    assert geo_ip._cache == {}
    assert geo_ip._cache_day == DAY + timedelta(days=1)
