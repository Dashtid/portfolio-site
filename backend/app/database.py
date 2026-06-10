"""
Database connection and session management
"""

import os
import time

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Determine if SQLite (which doesn't support pooling well with async)
is_sqlite = settings.async_database_url.startswith("sqlite")
is_postgres = settings.async_database_url.startswith("postgresql")

# Create async engine with production-ready settings
# SQLite doesn't support pool_size/max_overflow - must exclude them entirely
_engine_kwargs: dict = {
    "echo": settings.DEBUG and getattr(settings, "DEBUG_SQL", False),
    "future": True,
}

if is_sqlite:
    # SQLite: use NullPool (no connection pooling)
    _engine_kwargs["poolclass"] = NullPool
else:
    # PostgreSQL/MySQL: use connection pooling
    _engine_kwargs.update(
        {
            "pool_pre_ping": True,  # Validate connections before use
            "pool_recycle": 1800,  # Recycle connections every 30 minutes
            "pool_size": 5,  # Base pool size
            "max_overflow": 10,  # Additional connections when pool is full
        }
    )

if is_postgres:
    # Postgres server-side statement_timeout — caps the slowest single query at
    # DB_STATEMENT_TIMEOUT_MS so a runaway sequential scan can't hold a request
    # open for minutes. Set via asyncpg's `server_settings` connect arg, which
    # issues `SET LOCAL statement_timeout` per session at checkout. SQLite has
    # no equivalent — the same setting is silently a no-op there.
    _engine_kwargs.setdefault("connect_args", {})
    _engine_kwargs["connect_args"].setdefault("server_settings", {})
    _engine_kwargs["connect_args"]["server_settings"]["statement_timeout"] = str(
        settings.DB_STATEMENT_TIMEOUT_MS
    )

engine = create_async_engine(settings.async_database_url, **_engine_kwargs)


# Slow-query observability. before_cursor_execute stamps a start time on the
# connection's info dict; after_cursor_execute computes the delta and logs a
# WARNING line for anything over SLOW_QUERY_THRESHOLD_MS. The structured
# payload (sql, duration_ms, params count) flows through the JSON formatter so
# Fly/Sentry queries can filter on `slow_query=true`.
#
# Hooked on the underlying sync engine because SQLAlchemy fires DBAPI events
# at that level; async engines wrap a sync engine under the hood.
@event.listens_for(engine.sync_engine, "before_cursor_execute")
def _slow_query_before(_conn, _cursor, _statement, _parameters, context, _executemany) -> None:
    context._query_start_time = time.perf_counter()


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def _slow_query_after(_conn, _cursor, statement, parameters, context, _executemany) -> None:
    start = getattr(context, "_query_start_time", None)
    if start is None:
        return
    duration_ms = (time.perf_counter() - start) * 1000.0
    if duration_ms < settings.SLOW_QUERY_THRESHOLD_MS:
        return
    # Cap the SQL preview so a huge IN (...) clause doesn't blow up the log
    # line. The full query is still in pg_stat_statements / equivalent.
    sql_preview = (statement or "").strip()
    if len(sql_preview) > 500:
        sql_preview = sql_preview[:500] + "...<truncated>"
    logger.warning(
        "Slow query detected",
        extra={
            "slow_query": True,
            "duration_ms": round(duration_ms, 2),
            "threshold_ms": settings.SLOW_QUERY_THRESHOLD_MS,
            "sql": sql_preview,
            "params_count": len(parameters) if parameters else 0,
        },
    )


# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)

# Create base class for models
Base = declarative_base()


# Dependency to get database session
async def get_db():
    """
    Dependency function to get database session.
    Ensures proper cleanup with rollback on errors.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            # Rollback any uncommitted changes on error
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db(drop_existing: bool = False) -> None:
    """Create all tables defined on the metadata.

    Args:
        drop_existing: If True, drop all tables first. Requires the
            ALLOW_DB_DROP=true environment variable as a guard against
            accidental destructive runs.
    """
    async with engine.begin() as conn:
        if drop_existing:
            if os.getenv("ALLOW_DB_DROP", "").lower() != "true":
                logger.error("Cannot drop tables: set ALLOW_DB_DROP=true to allow it")
                raise RuntimeError("ALLOW_DB_DROP=true required to drop existing tables")
            logger.warning("Dropping all existing tables...")
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
