"""Tests for the background OSS-dashboard refresh in ``app.main``.

Context: until 2026-08-25 the dashboard refreshed only when a human clicked
the admin button. Nobody did for four weeks, so a NOT NULL crash inside
``refresh()`` stayed invisible while the homepage served a frozen strip.
The scheduler exists so freshness stops depending on someone remembering;
these tests pin the properties that make it safe to run unattended.
"""

import asyncio
import contextlib
from unittest.mock import patch

import pytest

from app.main import OSS_REFRESH_INTERVAL_SECONDS, refresh_oss_dashboard_periodically


class _Result:
    contributions_count = 7
    rate_limit_remaining = 4990


async def _run_one_iteration(monkeypatch, *, refresh):
    """Drive exactly one loop pass, then cancel out of the infinite loop."""
    calls = {"n": 0}
    real_sleep = asyncio.sleep

    async def fake_sleep(_delay):
        calls["n"] += 1
        if calls["n"] >= 2:
            raise asyncio.CancelledError
        await real_sleep(0)

    class _Service:
        def __init__(self):
            self.refresh = refresh

    with (
        patch("app.main.asyncio.sleep", fake_sleep),
        patch("app.services.oss_sync.oss_sync_service", _Service()),
        contextlib.suppress(asyncio.CancelledError),
    ):
        await refresh_oss_dashboard_periodically()


class TestScheduledOssRefresh:
    def test_interval_is_six_hours(self):
        """Cheap against a 5000/hour budget, and the cadence the sync
        service's own httpx-lifecycle comment already assumes."""
        assert OSS_REFRESH_INTERVAL_SECONDS == 6 * 60 * 60

    @pytest.mark.anyio
    async def test_sleeps_before_the_first_refresh(self, monkeypatch):
        """Boot must stay fast, and a crash-looping machine must not be able
        to hammer the GitHub API on every restart."""
        order = []

        async def refresh(_session):
            order.append("refresh")
            return _Result()

        real_sleep = asyncio.sleep
        calls = {"n": 0}

        async def fake_sleep(_delay):
            calls["n"] += 1
            order.append("sleep")
            if calls["n"] >= 2:
                raise asyncio.CancelledError
            await real_sleep(0)

        monkeypatch.setattr("app.config.settings.GITHUB_OSS_DASHBOARD_PAT", "token")

        class _Service:
            pass

        service = _Service()
        service.refresh = refresh

        with (
            patch("app.main.asyncio.sleep", fake_sleep),
            patch("app.services.oss_sync.oss_sync_service", service),
            contextlib.suppress(asyncio.CancelledError),
        ):
            await refresh_oss_dashboard_periodically()

        assert order[0] == "sleep"

    @pytest.mark.anyio
    async def test_a_github_failure_never_escapes_the_loop(self, monkeypatch):
        """A GitHub outage or an expired PAT must not take the API process
        down — the strip keeps serving the last good rows instead."""
        monkeypatch.setattr("app.config.settings.GITHUB_OSS_DASHBOARD_PAT", "token")
        called = {"n": 0}

        async def exploding_refresh(_session):
            called["n"] += 1
            raise RuntimeError("GitHub is down")

        # Must not raise.
        await _run_one_iteration(monkeypatch, refresh=exploding_refresh)
        # ...and it must have actually reached the refresh, or this test
        # would be passing for the wrong reason (a silently-failed patch
        # would skip the call and swallow nothing at all).
        assert called["n"] == 1

    @pytest.mark.anyio
    async def test_skips_entirely_when_no_pat_is_configured(self, monkeypatch):
        """No PAT (dev, CI, a fresh environment) means no pointless GitHub
        call and no error-log noise every six hours."""
        monkeypatch.setattr("app.config.settings.GITHUB_OSS_DASHBOARD_PAT", None)
        called = {"n": 0}

        async def refresh(_session):
            called["n"] += 1
            return _Result()

        await _run_one_iteration(monkeypatch, refresh=refresh)
        assert called["n"] == 0
