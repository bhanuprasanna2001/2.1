"""Tests for authentication endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, hash_password
from app.models import User

# ─────────────────────────────────────────────────────────────────────────────
# Registration Tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    """Test successful user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "display_name": "New User",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["display_name"] == "New User"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test registration with existing email fails."""
    # Create existing user
    existing_user = User(
        email="existing@example.com",
        hashed_password=hash_password("password123"),
        is_active=True,
    )
    db_session.add(existing_user)
    await db_session.commit()

    # Try to register with same email
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "existing@example.com",
            "password": "SecurePassword123!",
        },
    )

    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "DUPLICATE_RESOURCE"


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient) -> None:
    """Test registration with weak password fails validation."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "weak",  # Too short, no uppercase, no digit, no special
        },
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient) -> None:
    """Test registration with invalid email fails."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "notanemail",
            "password": "SecurePassword123!",
        },
    )

    assert response.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# Login Tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.usefixtures("test_user")
async def test_login_success(
    client: AsyncClient,
    test_user_email: str,
    test_user_password: str,
) -> None:
    """Test successful login returns tokens."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user_email,
            "password": test_user_password,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
@pytest.mark.usefixtures("test_user")
async def test_login_wrong_password(
    client: AsyncClient,
    test_user_email: str,
) -> None:
    """Test login with wrong password fails."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user_email,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient) -> None:
    """Test login with nonexistent email fails."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nobody@example.com",
            "password": "SomePassword123!",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test login with inactive account fails."""
    # Create inactive user
    inactive_user = User(
        email="inactive@example.com",
        hashed_password=hash_password("SecurePassword123!"),
        is_active=False,
    )
    db_session.add(inactive_user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "inactive@example.com",
            "password": "SecurePassword123!",
        },
    )

    assert response.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# Token Refresh Tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, test_user: User) -> None:
    """Test successful token refresh."""
    refresh_token = create_refresh_token(user_id=test_user.id, token_id=str(uuid4()))

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient) -> None:
    """Test refresh with invalid token fails."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.token.here"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_wrong_type(client: AsyncClient, test_user: User) -> None:
    """Test refresh with access token (wrong type) fails."""
    access_token = create_access_token(user_id=test_user.id)

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )

    assert response.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# Protected Endpoint Tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_me_endpoint_authenticated(
    client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
) -> None:
    """Test /me endpoint returns current user when authenticated."""
    # Override to not use mocked auth
    from app.api.deps import get_current_user_id
    from app.main import app

    app.dependency_overrides.pop(get_current_user_id, None)

    response = await client.get("/api/v1/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_me_endpoint_unauthenticated(client: AsyncClient) -> None:
    """Test /me endpoint requires authentication."""
    from app.api.deps import get_current_user_id
    from app.main import app

    app.dependency_overrides.pop(get_current_user_id, None)

    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_expired_token(client: AsyncClient, test_user: User) -> None:
    """Test expired token is rejected."""
    from datetime import timedelta

    from app.api.deps import get_current_user_id
    from app.core.security import create_access_token
    from app.main import app

    app.dependency_overrides.pop(get_current_user_id, None)

    # Create an expired token
    expired_token = create_access_token(
        user_id=test_user.id,
        expires_delta=timedelta(seconds=-1),  # Already expired
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# Logout Tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.usefixtures("test_user")
async def test_logout_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test logout endpoint succeeds."""
    from app.api.deps import get_current_user_id
    from app.main import app

    app.dependency_overrides.pop(get_current_user_id, None)

    response = await client.post("/api/v1/auth/logout", headers=auth_headers)

    # Logout is acknowledged (token invalidation would be in a blocklist
    # if fully implemented, but for now we return 200)
    assert response.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Security Module Unit Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_password_hashing() -> None:
    """Test password hashing and verification."""
    from app.core.security import hash_password, verify_password

    password = "SecurePassword123!"
    hashed = hash_password(password)

    # Hash should be different from original
    assert hashed != password

    # Verification should work
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_access_token_creation_and_verification() -> None:
    """Test access token creation and verification."""
    from app.core.security import create_access_token, verify_access_token

    user_id = uuid4()
    token = create_access_token(user_id=user_id)

    result = verify_access_token(token)
    assert result is not None
    assert result == user_id


def test_refresh_token_creation_and_verification() -> None:
    """Test refresh token creation and verification."""
    from app.core.security import create_refresh_token, verify_refresh_token

    user_id = uuid4()
    token_id = str(uuid4())
    token = create_refresh_token(user_id=user_id, token_id=token_id)

    result = verify_refresh_token(token)
    assert result is not None
    returned_user_id, returned_token_id = result
    assert returned_user_id == user_id
    assert returned_token_id == token_id


def test_access_token_not_valid_as_refresh() -> None:
    """Test that access token cannot be used as refresh token."""
    from app.core.security import create_access_token, verify_refresh_token

    user_id = uuid4()
    access_token = create_access_token(user_id=user_id)

    # Should fail because type is "access", not "refresh"
    payload = verify_refresh_token(access_token)
    assert payload is None


def test_refresh_token_not_valid_as_access() -> None:
    """Test that refresh token cannot be used as access token."""
    from app.core.security import create_refresh_token, verify_access_token

    user_id = uuid4()
    token_id = str(uuid4())
    refresh_token = create_refresh_token(user_id=user_id, token_id=token_id)

    # Should fail because type is "refresh", not "access"
    payload = verify_access_token(refresh_token)
    assert payload is None
