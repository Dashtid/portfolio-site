"""Tests for the daily visitor key: its format, its salt and the UTC day it lasts."""

import asyncio
import re
from collections.abc import Callable
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.utils import visitor_key
from app.utils.visitor_key import daily_visitor_key, rotate_daily_salt
from tests.conftest import run_one_cleanup_pass

ADDRESS = "203.0.113.5"
AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"
DAY = date(2030, 1, 1)


@pytest.fixture
def set_day(monkeypatch: pytest.MonkeyPatch) -> Callable[[date], None]:
    """Start from no salt on DAY; the returned setter moves the UTC date the module sees.

    monkeypatch puts the module's salt and date back after the test.
    """
    today = [DAY]
    monkeypatch.setattr(visitor_key, "_utc_today", lambda: today[0])
    monkeypatch.setattr(visitor_key, "_salt_day", None)
    monkeypatch.setattr(visitor_key, "_salt", b"")

    def move_to(day: date) -> None:
        today[0] = day

    return move_to


def test_the_key_is_v_and_16_hex_characters(set_day: Callable[[date], None]) -> None:
    assert re.fullmatch(r"v_[0-9a-f]{16}", daily_visitor_key(ADDRESS, AGENT))


def test_one_address_and_user_agent_keep_one_key_through_the_day(
    set_day: Callable[[date], None],
) -> None:
    assert daily_visitor_key(ADDRESS, AGENT) == daily_visitor_key(ADDRESS, AGENT)


def test_another_address_or_user_agent_gets_another_key(set_day: Callable[[date], None]) -> None:
    key = daily_visitor_key(ADDRESS, AGENT)
    assert daily_visitor_key("203.0.113.6", AGENT) != key
    assert daily_visitor_key(ADDRESS, AGENT + " extra") != key
    # The newline between the two parts keeps them apart.
    assert daily_visitor_key("a", "bc") != daily_visitor_key("ab", "c")


def test_a_user_agent_outside_ascii_gets_a_key(set_day: Callable[[date], None]) -> None:
    assert re.fullmatch(r"v_[0-9a-f]{16}", daily_visitor_key(ADDRESS, "Agent é\udcff"))


def test_the_key_changes_with_the_utc_date(set_day: Callable[[date], None]) -> None:
    first = daily_visitor_key(ADDRESS, AGENT)
    set_day(DAY + timedelta(days=1))
    second = daily_visitor_key(ADDRESS, AGENT)
    assert second != first
    assert daily_visitor_key(ADDRESS, AGENT) == second


def test_the_salt_is_what_secrets_token_bytes_returns_for_32(
    set_day: Callable[[date], None], monkeypatch: pytest.MonkeyPatch
) -> None:
    requested: list[int] = []
    drawn = bytes(range(32))

    def token_bytes(nbytes: int) -> bytes:
        requested.append(nbytes)
        return drawn

    monkeypatch.setattr(visitor_key, "secrets", SimpleNamespace(token_bytes=token_bytes))
    rotate_daily_salt()
    assert requested == [32]
    assert visitor_key._salt is drawn


def test_the_salt_is_drawn_once_per_utc_day(set_day: Callable[[date], None]) -> None:
    rotate_daily_salt()
    first = visitor_key._salt
    rotate_daily_salt()
    assert visitor_key._salt is first
    assert len(first) == 32
    set_day(DAY + timedelta(days=1))
    rotate_daily_salt()
    assert visitor_key._salt != first
    assert visitor_key._salt_day == DAY + timedelta(days=1)


def test_the_salt_is_not_derived_from_secret_key(
    set_day: Callable[[date], None], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two draws on one UTC day under one SECRET_KEY give two salts, and
    changing SECRET_KEY leaves the key of the day unchanged."""
    rotate_daily_salt()
    first = visitor_key._salt
    monkeypatch.setattr(visitor_key, "_salt_day", None)
    rotate_daily_salt()
    assert visitor_key._salt != first

    key = daily_visitor_key(ADDRESS, AGENT)
    monkeypatch.setattr(settings, "SECRET_KEY", "another-secret-key-of-at-least-32-chars")
    assert daily_visitor_key(ADDRESS, AGENT) == key


def test_a_cleanup_pass_replaces_the_salt_of_a_past_day(
    client: TestClient, set_day: Callable[[date], None]
) -> None:
    """The salt goes at the first cleanup pass of a new UTC day, beacon or not."""
    _ = client  # the pass deletes from tables the fixture creates
    rotate_daily_salt()
    first = visitor_key._salt
    set_day(DAY + timedelta(days=1))

    asyncio.run(run_one_cleanup_pass())

    assert visitor_key._salt_day == DAY + timedelta(days=1)
    assert visitor_key._salt != first
