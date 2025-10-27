"""
Test configuration and fixtures for pytest
"""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.security import create_access_token
from app.database import Base, get_db
from app.main import app

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    connect_args={"check_same_thread": False},
)

# Create test session
TestSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> TestClient:
    """Create a test client with overridden database dependency."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_token() -> str:
    """Create a test user access token."""
    return create_access_token(data={"sub": "test_user", "email": "test@example.com"})


@pytest.fixture
def test_admin_token() -> str:
    """Create a test admin access token."""
    return create_access_token(
        data={"sub": "admin_user", "email": "admin@example.com", "is_admin": True}
    )


@pytest.fixture
def auth_headers(test_user_token: str) -> dict:
    """Create authorization headers with user token."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def admin_headers(test_admin_token: str) -> dict:
    """Create authorization headers with admin token."""
    return {"Authorization": f"Bearer {test_admin_token}"}
