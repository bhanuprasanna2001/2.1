"""Bookmark repository for database operations."""

from enum import StrEnum
from uuid import UUID

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bookmark import Bookmark, BookmarkCollection, BookmarkTag
from app.models.collection import Collection
from app.models.tag import Tag
from app.repositories.base import BaseRepository


class SortField(StrEnum):
    """Available fields for sorting bookmarks."""

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    TITLE = "title"


class SortOrder(StrEnum):
    """Sort order options."""

    ASC = "asc"
    DESC = "desc"


class BookmarkRepository(BaseRepository[Bookmark]):
    """Repository for Bookmark entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize bookmark repository.

        Args:
            session: Async database session.
        """
        super().__init__(Bookmark, session)

    async def get_by_id_with_relations(
        self,
        bookmark_id: UUID,
        user_id: UUID,
    ) -> Bookmark | None:
        """Get a bookmark by ID with tags and collections loaded.

        Args:
            bookmark_id: The bookmark's UUID.
            user_id: The owner's UUID (for authorization).

        Returns:
            The bookmark if found and owned by user, None otherwise.
        """
        result = await self.session.execute(
            select(Bookmark)
            .options(selectinload(Bookmark.tags), selectinload(Bookmark.collections))
            .where(Bookmark.id == bookmark_id, Bookmark.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: UUID,
        *,
        offset: int = 0,
        limit: int = 20,
        is_favorite: bool | None = None,
        tag_id: UUID | None = None,
        collection_id: UUID | None = None,
        search: str | None = None,
        sort_by: SortField = SortField.CREATED_AT,
        sort_order: SortOrder = SortOrder.DESC,
    ) -> list[Bookmark]:
        """Get bookmarks for a user with filtering and sorting options.

        Args:
            user_id: The owner's UUID.
            offset: Number of records to skip.
            limit: Maximum number of records to return.
            is_favorite: Filter by favorite status.
            tag_id: Filter by tag.
            collection_id: Filter by collection.
            search: Search in title and description.
            sort_by: Field to sort by (created_at, updated_at, title).
            sort_order: Sort direction (asc, desc).

        Returns:
            List of bookmarks matching criteria.
        """
        query = (
            select(Bookmark)
            .options(selectinload(Bookmark.tags), selectinload(Bookmark.collections))
            .where(Bookmark.user_id == user_id)
        )

        if is_favorite is not None:
            query = query.where(Bookmark.is_favorite == is_favorite)

        if tag_id is not None:
            query = query.join(BookmarkTag).where(BookmarkTag.c.tag_id == tag_id)

        if collection_id is not None:
            query = query.join(BookmarkCollection).where(
                BookmarkCollection.c.collection_id == collection_id
            )

        if search:
            search_term = f"%{search}%"
            query = query.where(
                Bookmark.title.ilike(search_term) | Bookmark.description.ilike(search_term)
            )

        # Apply sorting
        sort_column = getattr(Bookmark, sort_by.value)
        order_func = desc if sort_order == SortOrder.DESC else asc
        query = query.order_by(order_func(sort_column))

        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_user(
        self,
        user_id: UUID,
        *,
        is_favorite: bool | None = None,
        tag_id: UUID | None = None,
        collection_id: UUID | None = None,
        search: str | None = None,
    ) -> int:
        """Count bookmarks for a user with filtering options.

        Args:
            user_id: The owner's UUID.
            is_favorite: Filter by favorite status.
            tag_id: Filter by tag.
            collection_id: Filter by collection.
            search: Search in title and description.

        Returns:
            Count of matching bookmarks.
        """
        query = select(func.count()).select_from(Bookmark).where(Bookmark.user_id == user_id)

        if is_favorite is not None:
            query = query.where(Bookmark.is_favorite == is_favorite)

        if tag_id is not None:
            query = query.join(BookmarkTag).where(BookmarkTag.c.tag_id == tag_id)

        if collection_id is not None:
            query = query.join(BookmarkCollection).where(
                BookmarkCollection.c.collection_id == collection_id
            )

        if search:
            search_term = f"%{search}%"
            query = query.where(
                Bookmark.title.ilike(search_term) | Bookmark.description.ilike(search_term)
            )

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_by_url(self, url: str, user_id: UUID) -> Bookmark | None:
        """Get a bookmark by URL for a specific user.

        Args:
            url: The bookmarked URL.
            user_id: The owner's UUID.

        Returns:
            The bookmark if found, None otherwise.
        """
        result = await self.session.execute(
            select(Bookmark).where(Bookmark.url == url, Bookmark.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_with_relations(
        self,
        user_id: UUID,
        url: str,
        title: str,
        description: str | None = None,
        favicon_url: str | None = None,
        is_favorite: bool = False,
        tag_ids: list[UUID] | None = None,
        collection_ids: list[UUID] | None = None,
    ) -> Bookmark:
        """Create a bookmark with tags and collections.

        Args:
            user_id: Owner's UUID.
            url: The URL to bookmark.
            title: Bookmark title.
            description: Optional description.
            favicon_url: Optional favicon URL.
            is_favorite: Favorite status.
            tag_ids: List of tag IDs to assign.
            collection_ids: List of collection IDs to add to.

        Returns:
            The created bookmark with relations loaded.
        """
        bookmark = Bookmark(
            user_id=user_id,
            url=url,
            title=title,
            description=description,
            favicon_url=favicon_url,
            is_favorite=is_favorite,
        )
        self.session.add(bookmark)
        await self.session.flush()

        # Add tags
        if tag_ids:
            tags_result = await self.session.execute(
                select(Tag).where(Tag.id.in_(tag_ids), Tag.user_id == user_id)
            )
            tags = list(tags_result.scalars().all())
            bookmark.tags = tags

        # Add collections
        if collection_ids:
            collections_result = await self.session.execute(
                select(Collection).where(
                    Collection.id.in_(collection_ids), Collection.user_id == user_id
                )
            )
            collections = list(collections_result.scalars().all())
            bookmark.collections = collections

        await self.session.flush()
        await self.session.refresh(bookmark)
        return bookmark

    async def update_relations(
        self,
        bookmark: Bookmark,
        user_id: UUID,
        tag_ids: list[UUID] | None = None,
        collection_ids: list[UUID] | None = None,
    ) -> Bookmark:
        """Update bookmark's tags and collections.

        Args:
            bookmark: The bookmark to update.
            user_id: Owner's UUID for validation.
            tag_ids: New list of tag IDs (replaces existing).
            collection_ids: New list of collection IDs (replaces existing).

        Returns:
            The updated bookmark.
        """
        if tag_ids is not None:
            tags_result = await self.session.execute(
                select(Tag).where(Tag.id.in_(tag_ids), Tag.user_id == user_id)
            )
            bookmark.tags = list(tags_result.scalars().all())

        if collection_ids is not None:
            collections_result = await self.session.execute(
                select(Collection).where(
                    Collection.id.in_(collection_ids), Collection.user_id == user_id
                )
            )
            bookmark.collections = list(collections_result.scalars().all())

        await self.session.flush()
        await self.session.refresh(bookmark)
        return bookmark
