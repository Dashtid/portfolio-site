"""
Tests for the OAuth state lifecycle: IP binding, TTL expiry, and periodic cleanup.

Covers BACKEND-TESTS-01 (IP-binding mismatch) and BACKEND-TESTS-02 (TTL +
cleanup). These tests exercise the database-backed CSRF state used by the
GitHub OAuth callback flow — the consume path lives in
``app.api.v1.auth.validate_and_consume_state`` and the periodic sweep lives
in ``app.main.cleanup_oauth_states_periodically``.

The IP-binding behaviour matters because the OAuth state acts as a CSRF
token; if the IP check is missing, an attacker who tricks the victim into
hitting a forged ``/auth/github`` link could replay the resulting state from
their own IP. The TTL/cleanup behaviour bounds how long stale or unused
state rows linger in the database.
"""

import asyncio
import contextlib
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.v1.auth import create_oauth_state, validate_and_consume_state
from app.main import cleanup_oauth_states_periodically
from app.models.oauth_state import OAuthState
from tests.conftest import TestSessionLocal


def _run(coro):
    """Run an async coroutine to completion in the test's own event loop."""
    return asyncio.run(coro)


class TestOAuthStateIpBinding:
    """BACKEND-TESTS-01: state consumption refuses cross-IP replay."""

    def test_state_consumed_by_originating_ip(self, client: TestClient):
        """The IP that created the state can consume it.

        Sanity check before the negative cases — if this fails the rest of
        the file is meaningless because every test would pass vacuously.
        """
        _ = client  # fixture ensures the schema exists

        async def go():
            async with TestSessionLocal() as session:
                state = await create_oauth_state(session, client_ip="203.0.113.5")
                return await validate_and_consume_state(session, state, client_ip="203.0.113.5")

        assert _run(go()) is True

    def test_state_rejected_from_different_ip(self, client: TestClient):
        """A different IP than the one that created the state cannot consume it.

        This is the CSRF protection: a forged OAuth init that lures the
        victim into ``/auth/github`` from THEIR IP cannot then be completed
        from the attacker's IP.
        """
        _ = client

        async def go():
            async with TestSessionLocal() as session:
                state = await create_oauth_state(session, client_ip="203.0.113.5")
                return await validate_and_consume_state(session, state, client_ip="198.51.100.42")

        assert _run(go()) is False

    def test_rejected_replay_does_not_consume_row(self, client: TestClient):
        """A wrong-IP attempt must NOT delete the legitimate row.

        Otherwise an attacker could DoS the real user's OAuth flow by
        firing wrong-IP callbacks faster than the user can complete theirs.
        The current implementation keys the DELETE...RETURNING on the IP
        match, so the row stays available for the real IP.
        """
        _ = client

        async def go():
            async with TestSessionLocal() as session:
                state = await create_oauth_state(session, client_ip="203.0.113.5")

            # Attacker tries from wrong IP — fails.
            async with TestSessionLocal() as session:
                bad = await validate_and_consume_state(session, state, client_ip="198.51.100.42")
                assert bad is False

            # Real user from correct IP — succeeds.
            async with TestSessionLocal() as session:
                return await validate_and_consume_state(session, state, client_ip="203.0.113.5")

        assert _run(go()) is True

    def test_unbound_state_accepts_any_ip(self, client: TestClient):
        """A state inserted without a client_ip (legacy / migration path) is
        consumable from any IP.

        We could have hardened this to require a non-NULL client_ip but the
        flow that creates them (``github_login``) always passes one. The
        permissive NULL case avoids breaking any in-flight states across
        rolling deploys.
        """
        _ = client

        async def go():
            async with TestSessionLocal() as session:
                state = await create_oauth_state(session, client_ip=None)
                return await validate_and_consume_state(session, state, client_ip="198.51.100.42")

        assert _run(go()) is True

    def test_state_is_single_use(self, client: TestClient):
        """Even from the originating IP, a state cannot be consumed twice.

        The DELETE...RETURNING is the single source of truth — a second
        call finds no matching row and returns False, regardless of IP.
        """
        _ = client

        async def go():
            async with TestSessionLocal() as session:
                state = await create_oauth_state(session, client_ip="203.0.113.5")

            async with TestSessionLocal() as session:
                first = await validate_and_consume_state(session, state, client_ip="203.0.113.5")
                assert first is True

            async with TestSessionLocal() as session:
                return await validate_and_consume_state(session, state, client_ip="203.0.113.5")

        assert _run(go()) is False


class TestOAuthStateTtl:
    """BACKEND-TESTS-02: expired states cannot be consumed; the periodic
    cleanup deletes them."""

    def test_expired_state_rejected(self, client: TestClient):
        """A state whose ``expires_at`` is in the past cannot be consumed
        even with the correct state value and matching IP."""
        _ = client

        async def go():
            past = datetime.now(UTC) - timedelta(minutes=1)
            async with TestSessionLocal() as session:
                expired = OAuthState(
                    state="expired-state-token-aaaa",
                    expires_at=past,
                    client_ip="203.0.113.5",
                )
                session.add(expired)
                await session.commit()

            async with TestSessionLocal() as session:
                return await validate_and_consume_state(
                    session, "expired-state-token-aaaa", client_ip="203.0.113.5"
                )

        assert _run(go()) is False

    def test_periodic_cleanup_deletes_expired_rows(self, client: TestClient):
        """One sweep of the background cleanup removes rows past their TTL.

        The production task sleeps 5 minutes between sweeps; we patch
        ``asyncio.sleep`` to fire instantly the first time and then cancel
        the task on the second sleep so the body executes exactly once.
        """
        _ = client

        async def go():
            now = datetime.now(UTC)
            async with TestSessionLocal() as session:
                session.add(
                    OAuthState(
                        state="expired-a-xxxxxxxxxxxx",
                        expires_at=now - timedelta(minutes=5),
                        client_ip="203.0.113.1",
                    )
                )
                session.add(
                    OAuthState(
                        state="expired-b-xxxxxxxxxxxx",
                        expires_at=now - timedelta(seconds=1),
                        client_ip="203.0.113.2",
                    )
                )
                session.add(
                    OAuthState(
                        state="fresh-xxxxxxxxxxxxxxxx",
                        expires_at=now + timedelta(minutes=5),
                        client_ip="203.0.113.3",
                    )
                )
                await session.commit()

            # Run exactly one body iteration: the first sleep returns
            # immediately, the second raises CancelledError to break out.
            call_count = {"n": 0}
            real_sleep = asyncio.sleep

            async def fake_sleep(_delay):
                call_count["n"] += 1
                if call_count["n"] >= 2:
                    raise asyncio.CancelledError
                await real_sleep(0)

            from unittest.mock import patch  # noqa: PLC0415

            # The cleanup function imports AsyncSessionLocal locally inside
            # the loop body to dodge a circular import; patching the symbol
            # on the database module catches it at lookup time.
            with (
                patch("app.main.asyncio.sleep", fake_sleep),
                patch("app.database.AsyncSessionLocal", TestSessionLocal),
                contextlib.suppress(asyncio.CancelledError),
            ):
                await cleanup_oauth_states_periodically()

            async with TestSessionLocal() as session:
                rows = (await session.execute(select(OAuthState))).scalars().all()
                return {row.state for row in rows}

        remaining = _run(go())
        assert "expired-a-xxxxxxxxxxxx" not in remaining
        assert "expired-b-xxxxxxxxxxxx" not in remaining
        assert "fresh-xxxxxxxxxxxxxxxx" in remaining

    def test_cleanup_loop_exits_on_cancellation(self, client: TestClient):
        """The cleanup loop's ``except CancelledError: break`` is reachable.

        The lifespan handler cancels this task on shutdown; the loop must
        break out cleanly rather than swallow the cancel and continue.
        """
        _ = client

        async def go():
            from unittest.mock import patch  # noqa: PLC0415

            async def cancel_immediately(_delay):
                raise asyncio.CancelledError

            with patch("app.main.asyncio.sleep", cancel_immediately):
                # The loop catches CancelledError and breaks; await
                # returns normally with no exception leaking out.
                await cleanup_oauth_states_periodically()

        _run(go())  # Should complete without raising.
