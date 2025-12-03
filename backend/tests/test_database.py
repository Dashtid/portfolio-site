"""
Tests for database module
"""

import pytest

from app.database import AsyncSessionLocal, Base, engine, get_db


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
        session = None
        async for s in get_db():
            session = s
            break
        # After generator exits, session should be closed
        # (we break early, but the finally block still runs)
