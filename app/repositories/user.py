"""User repository for database operations."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize user repository.

        Args:
            session: Async database session.
        """
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email address.

        Args:
            email: User's email address (case-insensitive).

        Returns:
            User if found, None otherwise.
        """
        result = await self.session.execute(
            select(User).where(func.lower(User.email) == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_id_active(self, user_id: UUID) -> User | None:
        """Get an active user by ID.

        Args:
            user_id: User's UUID.

        Returns:
            User if found and active, None otherwise.
        """
        result = await self.session.execute(
            select(User).where(User.id == user_id, User.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Check if an email is already registered.

        Args:
            email: Email address to check.

        Returns:
            True if email exists, False otherwise.
        """
        result = await self.session.execute(
            select(func.count()).where(func.lower(User.email) == email.lower())
        )
        return result.scalar_one() > 0

    async def create_user(
        self,
        email: str,
        hashed_password: str,
        display_name: str | None = None,
    ) -> User:
        """Create a new user.

        Args:
            email: User's email address.
            hashed_password: Pre-hashed password (Argon2).
            display_name: Optional display name.

        Returns:
            Created user entity.
        """
        user = User(
            email=email.lower(),  # Normalize email to lowercase
            hashed_password=hashed_password,
            display_name=display_name,
            is_active=True,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_password(self, user: User, hashed_password: str) -> User:
        """Update a user's password.

        Args:
            user: User entity to update.
            hashed_password: New pre-hashed password.

        Returns:
            Updated user entity.
        """
        user.hashed_password = hashed_password
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def deactivate(self, user: User) -> User:
        """Deactivate a user account.

        Args:
            user: User entity to deactivate.

        Returns:
            Updated user entity.
        """
        user.is_active = False
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_stats(self, user_id: UUID) -> dict[str, int]:
        """Get user statistics (bookmark, collection, tag counts).

        Args:
            user_id: User's UUID.

        Returns:
            Dictionary with counts.
        """
        from app.models.bookmark import Bookmark
        from app.models.collection import Collection
        from app.models.tag import Tag

        bookmark_count = await self.session.execute(
            select(func.count()).select_from(Bookmark).where(Bookmark.user_id == user_id)
        )
        collection_count = await self.session.execute(
            select(func.count()).select_from(Collection).where(Collection.user_id == user_id)
        )
        tag_count = await self.session.execute(
            select(func.count()).select_from(Tag).where(Tag.user_id == user_id)
        )

        return {
            "bookmark_count": bookmark_count.scalar_one(),
            "collection_count": collection_count.scalar_one(),
            "tag_count": tag_count.scalar_one(),
        }
