"""
Tests for database module
"""

import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_asyncio
from alembic.config import Config
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import StatementError

from alembic import command  # type: ignore[attr-defined]
from app.config import settings
from app.database import (
    AsyncSessionLocal,
    Base,
    _engine_kwargs,
    _slow_query_after,
    engine,
    get_db,
)
from app.models.analytics import PageView

_BACKEND_DIR = Path(__file__).resolve().parent.parent


class TestDatabaseModule:
    """Tests for database module components."""

    def test_engine_exists(self):
        """Test that async engine is created."""
        assert engine is not None

    def test_session_factory_exists(self):
        """Test that async session factory is created."""
        assert AsyncSessionLocal is not None

    def test_base_class_exists(self):
        """Test that Base class for models exists."""
        assert Base is not None
        assert hasattr(Base, "metadata")


class TestGetDb:
    """Tests for get_db dependency."""

    @pytest.mark.asyncio
    async def test_get_db_yields_session(self):
        """Test that get_db yields a session."""
        async for session in get_db():
            assert session is not None
            # Session should have standard SQLAlchemy methods
            assert hasattr(session, "commit")
            assert hasattr(session, "rollback")
            assert hasattr(session, "close")
            break

    @pytest.mark.asyncio
    async def test_get_db_closes_session(self):
        """Test that get_db properly closes session."""
        async for _ in get_db():
            # Just iterate once to test session creation
            break
        # After generator exits, session should be closed
        # (we break early, but the finally block still runs)


class TestBoundParametersHidden:
    """A failed statement's error text carries the SQL but not its values.

    str() of a StatementError is what the request, error-tracking and
    performance middleware log, and what every traceback prints.
    """

    MARKER = "contact-marker@example.test"

    async def _failed_update_text(self, tmp_path: Path, **engine_kwargs) -> str:
        """str() of the error an UPDATE raises when a trigger refuses it."""
        db = create_async_engine_for(tmp_path / "refused.db", **engine_kwargs)
        contacts = sa.Table(
            "contacts",
            sa.MetaData(),
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("email", sa.String),
        )
        try:
            async with db.begin() as conn:
                await conn.run_sync(contacts.metadata.create_all)
                await conn.execute(contacts.insert().values(id=1, email="old"))
                await conn.exec_driver_sql(
                    "CREATE TRIGGER refuse BEFORE UPDATE ON contacts "
                    "BEGIN SELECT RAISE(ABORT, 'update refused'); END"
                )
            with pytest.raises(StatementError) as exc_info:
                async with db.begin() as conn:
                    await conn.execute(contacts.update().values(email=self.MARKER))
            return str(exc_info.value)
        finally:
            await db.dispose()

    def test_app_engine_hides_parameters(self):
        assert _engine_kwargs["hide_parameters"] is True
        assert engine.sync_engine.hide_parameters is True

    async def test_app_setting_leaves_values_out_of_the_error(self, tmp_path: Path):
        hide = engine.sync_engine.hide_parameters
        text = await self._failed_update_text(tmp_path, hide_parameters=hide)
        assert "UPDATE contacts SET email" in text
        assert "[SQL parameters hidden due to hide_parameters=True]" in text
        assert self.MARKER not in text

    async def test_default_engine_would_print_the_values(self, tmp_path: Path):
        """The control: without the flag the bound value is in the text."""
        text = await self._failed_update_text(tmp_path)
        assert self.MARKER in text

    def test_migration_engine_hides_parameters(self, tmp_path: Path, monkeypatch):
        """alembic/env.py builds its own engine for the release-phase upgrade."""
        built: list[sa_asyncio.AsyncEngine] = []
        real = sa_asyncio.async_engine_from_config

        def spy(*args, **kwargs):
            built.append(real(*args, **kwargs))
            return built[-1]

        monkeypatch.setattr(sa_asyncio, "async_engine_from_config", spy)
        monkeypatch.setenv("ALEMBIC_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'env.db'}")
        # No ini file: env.py then skips logging.config.fileConfig, which would
        # disable the app's loggers for every test that runs after this one.
        config = Config()
        config.set_main_option("script_location", str(_BACKEND_DIR / "alembic"))

        command.current(config)

        assert built, "env.py did not build its engine through async_engine_from_config"
        assert all(e.sync_engine.hide_parameters is True for e in built)


class TestSlowQueryLine:
    """A statement slower than SLOW_QUERY_THRESHOLD_MS gets a "Slow query
    detected" line, except the two writes of a page view."""

    # The SQL of each statement as the app's engine and Postgres render it.
    DIALECTS = [engine.sync_engine.dialect, postgresql.dialect()]

    @staticmethod
    def _slow_lines(statement: sa.ClauseElement, dialect: sa.Dialect) -> int:
        """The slow-query lines the listener writes for `statement`, one second past the threshold."""
        context = SimpleNamespace(
            _query_start_time=time.perf_counter() - settings.SLOW_QUERY_THRESHOLD_MS / 1000 - 1
        )
        sql = str(statement.compile(dialect=dialect))
        with patch("app.database.logger") as mock_logger:
            _slow_query_after(None, None, sql, (), context, False)
        return mock_logger.warning.call_count

    @pytest.mark.parametrize("dialect", DIALECTS, ids=["app engine", "postgresql"])
    def test_the_writes_of_a_page_view_leave_no_line(self, dialect: sa.Dialect):
        # The beacon's INSERT and the country back-fill's UPDATE, as
        # app/api/v1/analytics.py builds them.
        beacon = sa.insert(PageView).values(id="x", page_path="/", referrer=None, session_id="v_0")
        backfill = sa.update(PageView).where(PageView.id == "x").values(country="SE")
        assert [self._slow_lines(s, dialect) for s in (beacon, backfill)] == [0, 0]

    @pytest.mark.parametrize("dialect", DIALECTS, ids=["app engine", "postgresql"])
    def test_other_slow_statements_keep_their_line(self, dialect: sa.Dialect):
        dashboard = sa.select(PageView.page_path).where(PageView.created_at >= sa.func.now())
        purge = sa.delete(PageView).where(PageView.created_at < sa.func.now())
        other = sa.insert(sa.table("page_views_archive", sa.column("id"))).values(id="x")
        assert [self._slow_lines(s, dialect) for s in (dashboard, purge, other)] == [1, 1, 1]


def create_async_engine_for(path: Path, **engine_kwargs) -> sa_asyncio.AsyncEngine:
    """A file-backed aiosqlite engine with the given create_engine options."""
    return sa_asyncio.create_async_engine(f"sqlite+aiosqlite:///{path}", **engine_kwargs)
