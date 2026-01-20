"""Pytest configuration and fixtures."""

from collections.abc import AsyncGenerator
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_current_user_id, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Base, User

# Test database URL (use SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

# Test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Test user constants
TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "TestPassword123!"


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test.

    Creates all tables before the test and drops them after.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database."""
    user = User(
        id=TEST_USER_ID,
        email=TEST_USER_EMAIL,
        hashed_password=hash_password(TEST_USER_PASSWORD),
        display_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user: User) -> str:
    """Create an authentication token for the test user."""
    return create_access_token(user_id=test_user.id)


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    """Create authentication headers for API requests."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with overridden dependencies."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def override_get_current_user_id() -> UUID:
        return TEST_USER_ID

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("test_user")
async def authenticated_client(
    db_session: AsyncSession,
    auth_headers: dict[str, str],
) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client that uses real JWT authentication.

    This fixture does NOT override the auth dependency, so it tests
    the actual authentication flow.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # Note: We do NOT override get_current_user_id to test real auth

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=auth_headers,
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_id() -> UUID:
    """Get the test user ID."""
    return TEST_USER_ID


@pytest.fixture
def test_user_email() -> str:
    """Get the test user email."""
    return TEST_USER_EMAIL


@pytest.fixture
def test_user_password() -> str:
    """Get the test user password."""
    return TEST_USER_PASSWORD
