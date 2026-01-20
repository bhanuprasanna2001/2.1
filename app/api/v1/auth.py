"""Authentication endpoints for user registration, login, and token management."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.deps import AuthServiceDep, CurrentUserID
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.base import MessageResponse
from app.schemas.user import UserCreate, UserRead

router = APIRouter()

# HTTP Bearer scheme for token extraction
bearer_scheme = HTTPBearer(auto_error=False)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password.",
)
async def register(
    data: UserCreate,
    service: AuthServiceDep,
) -> UserRead:
    """Register a new user account.

    - **email**: Valid email address (must be unique)
    - **password**: Password (min 8 characters, must contain letter and number)
    - **display_name**: Optional display name

    Returns the created user profile (without sensitive data).
    """
    return await service.register(data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Authenticate with email and password to obtain access and refresh tokens.",
)
async def login(
    data: LoginRequest,
    service: AuthServiceDep,
) -> TokenResponse:
    """Authenticate and obtain tokens.

    - **email**: Registered email address
    - **password**: Account password

    Returns:
    - **access_token**: JWT for API authentication (15 min expiry)
    - **refresh_token**: JWT for obtaining new access tokens (7 days expiry)
    - **expires_in**: Access token expiration in seconds
    """
    return await service.login(data)


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Refresh access token",
    description="Obtain a new access token using a valid refresh token.",
)
async def refresh_token(
    data: RefreshRequest,
    service: AuthServiceDep,
) -> AccessTokenResponse:
    """Refresh an access token.

    Use this endpoint when your access token expires to obtain a new one
    without requiring the user to log in again.

    - **refresh_token**: Valid refresh token from login

    Returns a new access token.
    """
    return await service.refresh(data.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout",
    description="Logout the current user. Client should discard tokens.",
)
async def logout(
    _credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> MessageResponse:
    """Logout the current user.

    This is a stateless operation - the server doesn't track tokens.
    The client should:
    1. Discard the access token
    2. Discard the refresh token
    3. Clear any cached user data

    For enhanced security, consider implementing a token blacklist
    (not included in this stateless implementation).
    """
    return MessageResponse(message="Successfully logged out")


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user",
    description="Get the authenticated user's profile.",
)
async def get_current_user(
    user_id: CurrentUserID,
    service: AuthServiceDep,
) -> UserRead:
    """Get current authenticated user's profile.

    Returns the user profile including:
    - Basic info (id, email, display_name)
    - Account status (is_active)
    - Timestamps (created_at, updated_at)
    - Statistics (bookmark_count, collection_count, tag_count)

    Requires valid access token in Authorization header.
    """
    return await service.get_current_user(user_id)
