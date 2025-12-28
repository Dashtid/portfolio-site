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
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DEBUG
    and getattr(settings, "DEBUG_SQL", False),  # Only log SQL if explicitly enabled
    future=True,
    # Pool settings (not applicable for SQLite async)
    pool_pre_ping=not is_sqlite,  # Validate connections before use (prevents stale connections)
    pool_recycle=1800 if not is_sqlite else -1,  # Recycle connections every 30 minutes
    pool_size=5 if not is_sqlite else 0,  # Base pool size
    max_overflow=10 if not is_sqlite else 0,  # Additional connections when pool is full
    # Use NullPool for SQLite (no connection pooling)
    poolclass=NullPool if is_sqlite else None,
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
