"""
Database connection and session management
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.config import settings

# Determine if SQLite (which doesn't support pooling well with async)
is_sqlite = settings.async_database_url.startswith("sqlite")

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

engine = create_async_engine(settings.async_database_url, **_engine_kwargs)

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
