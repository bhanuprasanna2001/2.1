"""Collection repository for database operations."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bookmark import BookmarkCollection
from app.models.collection import Collection
from app.repositories.base import BaseRepository


class CollectionRepository(BaseRepository[Collection]):
    """Repository for Collection entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize collection repository.

        Args:
            session: Async database session.
        """
        super().__init__(Collection, session)

    async def get_by_id_with_relations(
        self,
        collection_id: UUID,
        user_id: UUID,
    ) -> Collection | None:
        """Get a collection by ID with children and bookmarks loaded.

        Args:
            collection_id: The collection's UUID.
            user_id: The owner's UUID (for authorization).

        Returns:
            The collection if found and owned by user, None otherwise.
        """
        result = await self.session.execute(
            select(Collection)
            .options(
                selectinload(Collection.children),
                selectinload(Collection.bookmarks),
            )
            .where(Collection.id == collection_id, Collection.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
        parent_id: UUID | None = None,
        root_only: bool = False,
    ) -> list[Collection]:
        """Get collections for a user.

        Args:
            user_id: The owner's UUID.
            offset: Number of records to skip.
            limit: Maximum number of records to return.
            parent_id: Filter by parent collection.
            root_only: Only return root-level collections (no parent).

        Returns:
            List of collections.
        """
        query = (
            select(Collection)
            .options(selectinload(Collection.children))
            .where(Collection.user_id == user_id)
        )

        if root_only:
            query = query.where(Collection.parent_id.is_(None))
        elif parent_id is not None:
            query = query.where(Collection.parent_id == parent_id)

        query = query.order_by(Collection.name).offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_user(
        self,
        user_id: UUID,
        *,
        parent_id: UUID | None = None,
        root_only: bool = False,
    ) -> int:
        """Count collections for a user.

        Args:
            user_id: The owner's UUID.
            parent_id: Filter by parent collection.
            root_only: Only count root-level collections.

        Returns:
            Count of collections.
        """
        query = select(func.count()).select_from(Collection).where(Collection.user_id == user_id)

        if root_only:
            query = query.where(Collection.parent_id.is_(None))
        elif parent_id is not None:
            query = query.where(Collection.parent_id == parent_id)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_bookmark_count(self, collection_id: UUID) -> int:
        """Get count of bookmarks in a collection.

        Args:
            collection_id: The collection's UUID.

        Returns:
            Number of bookmarks.
        """
        result = await self.session.execute(
            select(func.count())
            .select_from(BookmarkCollection)
            .where(BookmarkCollection.c.collection_id == collection_id)
        )
        return result.scalar_one()

    async def get_by_name(self, name: str, user_id: UUID) -> Collection | None:
        """Get a collection by name for a specific user.

        Args:
            name: The collection name.
            user_id: The owner's UUID.

        Returns:
            The collection if found, None otherwise.
        """
        result = await self.session.execute(
            select(Collection).where(Collection.name == name, Collection.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def is_valid_parent(
        self,
        collection_id: UUID,
        parent_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Check if a parent_id is valid (not creating a cycle).

        A parent is invalid if:
        - It's the same as the collection itself
        - It's a descendant of the collection

        Args:
            collection_id: The collection being updated.
            parent_id: The proposed parent ID.
            user_id: The owner's UUID.

        Returns:
            True if valid, False if would create cycle.
        """
        if collection_id == parent_id:
            return False

        # Check if parent_id is a descendant of collection_id
        # by walking up the tree from parent_id
        current_id: UUID | None = parent_id
        visited: set[UUID] = set()

        while current_id is not None:
            if current_id in visited:
                # Cycle detected in existing data (shouldn't happen)
                return False
            if current_id == collection_id:
                # Would create a cycle
                return False
            visited.add(current_id)

            result = await self.session.execute(
                select(Collection.parent_id).where(
                    Collection.id == current_id, Collection.user_id == user_id
                )
            )
            row = result.one_or_none()
            current_id = row[0] if row else None

        return True
