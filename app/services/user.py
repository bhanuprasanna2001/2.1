"""User service for user profile management."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ErrorCode, NotFoundError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserRead, UserUpdate, UserUpdatePassword


class UserService:
    """Service for user profile operations.

    Handles user profile viewing, updating, and password changes.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize user service.

        Args:
            session: Async database session.
        """
        self.session = session
        self.repository = UserRepository(session)

    async def get_by_id(self, user_id: UUID) -> UserRead:
        """Get a user by ID.

        Args:
            user_id: User's UUID.

        Returns:
            User profile.

        Raises:
            NotFoundError: If user not found.
        """
        user = await self.repository.get_by_id_active(user_id)
        if user is None:
            raise NotFoundError(
                resource="User",
                resource_id=user_id,
                code=ErrorCode.USER_NOT_FOUND,
            )
        return await self._to_user_read_with_stats(user)

    async def update(self, user_id: UUID, data: UserUpdate) -> UserRead:
        """Update user profile.

        Args:
            user_id: User's UUID.
            data: Update data.

        Returns:
            Updated user profile.

        Raises:
            NotFoundError: If user not found.
        """
        user = await self.repository.get_by_id_active(user_id)
        if user is None:
            raise NotFoundError(
                resource="User",
                resource_id=user_id,
                code=ErrorCode.USER_NOT_FOUND,
            )

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            for key, value in update_data.items():
                setattr(user, key, value)
            await self.session.flush()
            await self.session.refresh(user)

        return await self._to_user_read_with_stats(user)

    async def change_password(
        self,
        user_id: UUID,
        data: UserUpdatePassword,
    ) -> UserRead:
        """Change user's password.

        Args:
            user_id: User's UUID.
            data: Current and new passwords.

        Returns:
            Updated user profile.

        Raises:
            NotFoundError: If user not found.
            AuthenticationError: If current password is incorrect.
        """
        user = await self.repository.get_by_id_active(user_id)
        if user is None:
            raise NotFoundError(
                resource="User",
                resource_id=user_id,
                code=ErrorCode.USER_NOT_FOUND,
            )

        # Verify current password
        if not verify_password(data.current_password, user.hashed_password):
            raise AuthenticationError(
                message="Current password is incorrect",
                code=ErrorCode.INVALID_CREDENTIALS,
            )

        # Update password
        hashed_password = hash_password(data.new_password)
        await self.repository.update_password(user, hashed_password)

        return await self._to_user_read_with_stats(user)

    async def deactivate(self, user_id: UUID, password: str) -> None:
        """Deactivate user account.

        Requires password confirmation for security.

        Args:
            user_id: User's UUID.
            password: Password for confirmation.

        Raises:
            NotFoundError: If user not found.
            AuthenticationError: If password is incorrect.
        """
        user = await self.repository.get_by_id_active(user_id)
        if user is None:
            raise NotFoundError(
                resource="User",
                resource_id=user_id,
                code=ErrorCode.USER_NOT_FOUND,
            )

        # Verify password
        if not verify_password(password, user.hashed_password):
            raise AuthenticationError(
                message="Password is incorrect",
                code=ErrorCode.INVALID_CREDENTIALS,
            )

        await self.repository.deactivate(user)

    async def _to_user_read_with_stats(self, user: User) -> UserRead:
        """Convert User entity to UserRead schema with statistics.

        Args:
            user: User entity.

        Returns:
            UserRead schema with counts.
        """
        stats = await self.repository.get_stats(user.id)
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
