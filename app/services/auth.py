"""Authentication service for user authentication and token management."""

import uuid
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import AuthenticationError, ConflictError, ErrorCode
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_refresh_token,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import AccessTokenResponse, LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead


class AuthService:
    """Service for authentication operations.

    Handles user registration, login, token refresh, and logout.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize auth service.

        Args:
            session: Async database session.
        """
        self.session = session
        self.user_repository = UserRepository(session)

    async def register(self, data: UserCreate) -> UserRead:
        """Register a new user.

        Args:
            data: User registration data.

        Returns:
            Created user profile.

        Raises:
            ConflictError: If email is already registered.
        """
        # Check for existing email
        if await self.user_repository.email_exists(data.email):
            raise ConflictError(
                resource="User",
                field="email",
                value=data.email,
            )

        # Hash password and create user
        hashed_password = hash_password(data.password)
        user = await self.user_repository.create_user(
            email=data.email,
            hashed_password=hashed_password,
            display_name=data.display_name,
        )

        return self._to_user_read(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate user and generate tokens.

        Args:
            data: Login credentials.

        Returns:
            Access and refresh tokens.

        Raises:
            AuthenticationError: If credentials are invalid.
        """
        # Find user by email
        user = await self.user_repository.get_by_email(data.email)
        if user is None:
            # Use constant-time comparison even for non-existent users
            # to prevent timing attacks
            verify_password(data.password, "$argon2id$v=19$m=65536,t=3,p=4$dummy$dummy")
            raise AuthenticationError(
                message="Invalid email or password",
                code=ErrorCode.INVALID_CREDENTIALS,
            )

        # Check if user is active
        if not user.is_active:
            raise AuthenticationError(
                message="Account is deactivated",
                code=ErrorCode.INVALID_CREDENTIALS,
            )

        # Verify password
        if not verify_password(data.password, user.hashed_password):
            raise AuthenticationError(
                message="Invalid email or password",
                code=ErrorCode.INVALID_CREDENTIALS,
            )

        # Generate tokens
        return self._create_token_response(user.id)

    async def refresh(self, refresh_token: str) -> AccessTokenResponse:
        """Refresh an access token using a valid refresh token.

        Args:
            refresh_token: Valid refresh token.

        Returns:
            New access token.

        Raises:
            AuthenticationError: If refresh token is invalid or expired.
        """
        # Verify refresh token
        result = verify_refresh_token(refresh_token)
        if result is None:
            raise AuthenticationError(
                message="Invalid or expired refresh token",
                code=ErrorCode.TOKEN_INVALID,
            )

        user_id, _token_id = result

        # Verify user still exists and is active
        user = await self.user_repository.get_by_id_active(user_id)
        if user is None:
            raise AuthenticationError(
                message="User not found or deactivated",
                code=ErrorCode.TOKEN_INVALID,
            )

        # Generate new access token
        access_token = create_access_token(user_id)
        return AccessTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def get_current_user(self, user_id: UUID) -> UserRead:
        """Get current authenticated user profile.

        Args:
            user_id: User's UUID from token.

        Returns:
            User profile with statistics.

        Raises:
            AuthenticationError: If user not found or deactivated.
        """
        user = await self.user_repository.get_by_id_active(user_id)
        if user is None:
            raise AuthenticationError(
                message="User not found or deactivated",
                code=ErrorCode.UNAUTHORIZED,
            )

        return await self._to_user_read_with_stats(user)

    def _create_token_response(self, user_id: UUID) -> TokenResponse:
        """Create access and refresh token response.

        Args:
            user_id: User's UUID.

        Returns:
            Token response with both tokens.
        """
        # Generate unique token ID for refresh token
        token_id = str(uuid.uuid4())

        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id, token_id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    def _to_user_read(self, user: User) -> UserRead:
        """Convert User entity to UserRead schema.

        Args:
            user: User entity.

        Returns:
            UserRead schema.
        """
        return UserRead(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            bookmark_count=0,
            collection_count=0,
            tag_count=0,
        )

    async def _to_user_read_with_stats(self, user: User) -> UserRead:
        """Convert User entity to UserRead schema with statistics.

        Args:
            user: User entity.

        Returns:
            UserRead schema with counts.
        """
        stats = await self.user_repository.get_stats(user.id)
        return UserRead(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            bookmark_count=stats["bookmark_count"],
            collection_count=stats["collection_count"],
            tag_count=stats["tag_count"],
        )
