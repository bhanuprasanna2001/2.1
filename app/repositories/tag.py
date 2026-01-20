"""Tag repository for database operations."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bookmark import BookmarkTag
from app.models.tag import Tag
from app.repositories.base import BaseRepository


class TagRepository(BaseRepository[Tag]):
    """Repository for Tag entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize tag repository.

        Args:
            session: Async database session.
        """
        super().__init__(Tag, session)

    async def get_by_id_for_user(
        self,
        tag_id: UUID,
        user_id: UUID,
    ) -> Tag | None:
        """Get a tag by ID for a specific user.

        Args:
            tag_id: The tag's UUID.
            user_id: The owner's UUID (for authorization).

        Returns:
            The tag if found and owned by user, None otherwise.
        """
        result = await self.session.execute(
            select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> list[Tag]:
        """Get tags for a user.

        Args:
            user_id: The owner's UUID.
            offset: Number of records to skip.
            limit: Maximum number of records to return.
            search: Search in tag name.

        Returns:
            List of tags.
        """
        query = select(Tag).where(Tag.user_id == user_id)

        if search:
            search_term = f"%{search.lower()}%"
            query = query.where(Tag.name.ilike(search_term))

        query = query.order_by(Tag.name).offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_user(
        self,
        user_id: UUID,
        *,
        search: str | None = None,
    ) -> int:
        """Count tags for a user.

        Args:
            user_id: The owner's UUID.
            search: Search in tag name.

        Returns:
            Count of tags.
        """
        query = select(func.count()).select_from(Tag).where(Tag.user_id == user_id)

        if search:
            search_term = f"%{search.lower()}%"
            query = query.where(Tag.name.ilike(search_term))

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_bookmark_count(self, tag_id: UUID) -> int:
        """Get count of bookmarks with this tag.

        Args:
            tag_id: The tag's UUID.

        Returns:
            Number of bookmarks.
        """
        result = await self.session.execute(
            select(func.count()).select_from(BookmarkTag).where(BookmarkTag.c.tag_id == tag_id)
        )
        return result.scalar_one()

    async def get_by_name(self, name: str, user_id: UUID) -> Tag | None:
        """Get a tag by name for a specific user.

        Args:
            name: The tag name (will be lowercased).
            user_id: The owner's UUID.

        Returns:
            The tag if found, None otherwise.
        """
        result = await self.session.execute(
            select(Tag).where(Tag.name == name.lower(), Tag.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        name: str,
        user_id: UUID,
        color: str | None = None,
    ) -> tuple[Tag, bool]:
        """Get existing tag or create new one.

        Args:
            name: Tag name.
            user_id: Owner's UUID.
            color: Optional color for new tags.

        Returns:
            Tuple of (tag, created) where created is True if new.
        """
        existing = await self.get_by_name(name, user_id)
        if existing:
            return existing, False

        tag = await self.create(
            user_id=user_id,
            name=name.lower().strip(),
            color=color,
        )
        return tag, True

    async def get_by_ids(self, tag_ids: list[UUID], user_id: UUID) -> list[Tag]:
        """Get multiple tags by IDs for a user.

        Args:
            tag_ids: List of tag UUIDs.
            user_id: The owner's UUID.

        Returns:
            List of tags (only those owned by user).
        """
        if not tag_ids:
            return []

        result = await self.session.execute(
            select(Tag).where(Tag.id.in_(tag_ids), Tag.user_id == user_id)
        )
        return list(result.scalars().all())
