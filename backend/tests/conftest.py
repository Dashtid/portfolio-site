"""
Test configuration and fixtures for pytest
"""

import asyncio
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.database import Base, get_db
from app.main import app
from app.middleware import limiter

# Import all models to ensure they're registered with Base.metadata
from app.models.analytics import PageView  # noqa: F401
from app.models.company import Company  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.education import Education  # noqa: F401
from app.models.oauth_state import OAuthState  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.skill import Skill  # noqa: F401
from app.models.user import User  # noqa: F401

# Test database URL - use file-based SQLite for test isolation
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine with StaticPool to share connection across async operations
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)


# SQLite ignores ondelete="CASCADE" unless `PRAGMA foreign_keys = ON` is set
# per connection. Production runs Postgres which enforces FKs by default; we
# enable the pragma in tests so cascade-delete behaviour stays in test/prod
# parity and so an orphaned-row insert fails loudly instead of silently.
@event.listens_for(test_engine.sync_engine, "connect")
def _enable_sqlite_fk(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


# Create test session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, Any, None]:
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, Any, None]:
    """Create a test client with fresh database tables for each test."""

    async def setup_db():
        """Create all tables in the test database."""
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def teardown_db():
        """Drop all tables after test."""
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def get_test_db():
        """Override database dependency."""
        async with TestSessionLocal() as session:
            try:
                yield session
            finally:
                await session.rollback()

    # Create tables before test using asyncio.run for proper event loop handling
    asyncio.run(setup_db())

    # Override the database dependency
    app.dependency_overrides[get_db] = get_test_db

    # Reset rate limiter storage before each test to prevent rate limit interference
    limiter.reset()

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()
    asyncio.run(teardown_db())


@pytest.fixture
def test_user_token() -> str:
    """Create a test user access token."""
    return create_access_token(subject="test_user")


@pytest.fixture
def test_admin_token() -> str:
    """Create a test admin access token."""
    return create_access_token(subject="admin_user")


@pytest.fixture
def auth_headers(test_user_token: str) -> dict[str, str]:
    """Create authorization headers with user token."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def admin_headers(test_admin_token: str) -> dict[str, str]:
    """Create authorization headers with admin token."""
    return {"Authorization": f"Bearer {test_admin_token}"}


def _seed_user_with_tokens(
    *,
    user_id: str,
    github_id: str,
    username: str,
    email: str,
    name: str,
    avatar_url: str,
    is_admin: bool,
) -> dict[str, Any]:
    """Create the user row + a server-side refresh-token record, mint tokens."""
    import asyncio

    from app.core.security import create_refresh_token
    from app.models.refresh_token import RefreshToken as _RefreshToken

    access_token = create_access_token(subject=user_id)
    refresh_token, refresh_jti, refresh_exp = create_refresh_token(subject=user_id)

    async def setup():
        async with TestSessionLocal() as session:
            user = User(
                id=user_id,
                github_id=github_id,
                username=username,
                email=email,
                name=name,
                avatar_url=avatar_url,
                is_admin=is_admin,
            )
            session.add(user)
            # Commit the user first so the FK on refresh_tokens.user_id has
            # a target row by the time we insert the token. SQLAlchemy does
            # not automatically order dependency-only inserts when no
            # relationship() is declared on the model.
            await session.commit()
            session.add(_RefreshToken(jti=refresh_jti, user_id=user_id, expires_at=refresh_exp))
            await session.commit()

    asyncio.run(setup())

    return {
        "user_id": user_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh_jti": refresh_jti,
        "headers": {"Authorization": f"Bearer {access_token}"},
    }


@pytest.fixture
def test_user_in_db(client: TestClient) -> dict[str, Any]:
    """Create a test user in the database and return user data with tokens."""
    return _seed_user_with_tokens(
        user_id="test-user-id-12345",
        github_id="12345",
        username="testuser",
        email="test@example.com",
        name="Test User",
        avatar_url="https://example.com/avatar.png",
        is_admin=False,
    )


@pytest.fixture
def admin_user_in_db(client: TestClient) -> dict[str, Any]:
    """Create an admin user in the database and return user data with tokens."""
    return _seed_user_with_tokens(
        user_id="admin-user-id-12345",
        github_id="67890",
        username="adminuser",
        email="admin@example.com",
        name="Admin User",
        avatar_url="https://example.com/admin-avatar.png",
        is_admin=True,
    )
