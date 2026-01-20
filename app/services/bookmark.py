"""Bookmark service for business logic."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ConflictError, ErrorCode, NotFoundError
from app.models.bookmark import Bookmark
from app.repositories.bookmark import BookmarkRepository, SortField, SortOrder
from app.schemas.base import PaginatedResponse
from app.schemas.bookmark import BookmarkCreate, BookmarkRead, BookmarkUpdate
from app.utils.metadata import fetch_url_metadata


class BookmarkService:
    """Service for bookmark business logic.

    Handles operations on bookmarks including validation,
    authorization checks, and coordinating with repositories.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service with database session.

        Args:
            session: Async database session.
        """
        self.session = session
        self.repository = BookmarkRepository(session)

    async def create(
        self,
        user_id: UUID,
        data: BookmarkCreate,
        *,
        auto_fetch_metadata: bool | None = None,
    ) -> BookmarkRead:
        """Create a new bookmark.

        Args:
            user_id: Owner's UUID.
            data: Bookmark creation data.
            auto_fetch_metadata: Override setting to auto-fetch URL metadata.
                If None, uses the global settings value.

        Returns:
            Created bookmark.

        Raises:
            ConflictError: If URL already bookmarked by user.
        """
        # Check for duplicate URL
        existing = await self.repository.get_by_url(data.url, user_id)
        if existing:
            raise ConflictError(
                resource="Bookmark",
                field="url",
                value=data.url,
            )

        # Determine if we should auto-fetch metadata
        should_fetch = (
            auto_fetch_metadata
            if auto_fetch_metadata is not None
            else settings.metadata_fetch_enabled
        )

        title = data.title
        description = data.description
        favicon_url = None

        # Auto-fetch metadata if enabled and title is a placeholder or URL
        if should_fetch:
            metadata = await fetch_url_metadata(data.url)
            # Only use fetched title if user didn't provide a meaningful one
            if metadata.title and (not title or title == data.url):
                title = metadata.title
            # Only use fetched description if user didn't provide one
            if metadata.description and not description:
                description = metadata.description
            # Always use fetched favicon if available
            if metadata.favicon_url:
                favicon_url = metadata.favicon_url

        bookmark = await self.repository.create_with_relations(
            user_id=user_id,
            url=data.url,
            title=title,
            description=description,
            favicon_url=favicon_url,
            is_favorite=data.is_favorite,
            tag_ids=data.tag_ids or [],
            collection_ids=data.collection_ids or [],
        )

        return self._to_read_schema(bookmark)

    async def get_by_id(
        self,
        bookmark_id: UUID,
        user_id: UUID,
    ) -> BookmarkRead:
        """Get a bookmark by ID.

        Args:
            bookmark_id: Bookmark's UUID.
            user_id: Owner's UUID for authorization.

        Returns:
            Bookmark data.

        Raises:
            NotFoundError: If bookmark not found or not owned by user.
        """
        bookmark = await self.repository.get_by_id_with_relations(bookmark_id, user_id)
        if not bookmark:
            raise NotFoundError(
                resource="Bookmark",
                resource_id=bookmark_id,
                code=ErrorCode.BOOKMARK_NOT_FOUND,
            )
        return self._to_read_schema(bookmark)

    async def list(
        self,
        user_id: UUID,
        *,
        page: int = 1,
        limit: int = 20,
        is_favorite: bool | None = None,
        tag_id: UUID | None = None,
        collection_id: UUID | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> PaginatedResponse[BookmarkRead]:
        """List bookmarks for a user with filtering and sorting.

        Args:
            user_id: Owner's UUID.
            page: Page number (1-indexed).
            limit: Items per page.
            is_favorite: Filter by favorite status.
            tag_id: Filter by tag.
            collection_id: Filter by collection.
            search: Search in title and description.
            sort_by: Field to sort by (created_at, updated_at, title).
            sort_order: Sort direction (asc, desc).

        Returns:
            Paginated list of bookmarks.
        """
        offset = (page - 1) * limit

        # Convert string params to enums (with validation)
        try:
            sort_field = SortField(sort_by)
        except ValueError:
            sort_field = SortField.CREATED_AT

        try:
            order = SortOrder(sort_order)
        except ValueError:
            order = SortOrder.DESC

        bookmarks = await self.repository.get_by_user(
            user_id,
            offset=offset,
            limit=limit,
            is_favorite=is_favorite,
            tag_id=tag_id,
            collection_id=collection_id,
            search=search,
            sort_by=sort_field,
            sort_order=order,
        )

        total = await self.repository.count_by_user(
            user_id,
            is_favorite=is_favorite,
            tag_id=tag_id,
            collection_id=collection_id,
            search=search,
        )

        items = [self._to_read_schema(b) for b in bookmarks]

        return PaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            limit=limit,
        )

    async def update(
        self,
        bookmark_id: UUID,
        user_id: UUID,
        data: BookmarkUpdate,
    ) -> BookmarkRead:
        """Update a bookmark.

        Args:
            bookmark_id: Bookmark's UUID.
            user_id: Owner's UUID for authorization.
            data: Update data.

        Returns:
            Updated bookmark.

        Raises:
            NotFoundError: If bookmark not found or not owned by user.
            ConflictError: If updating URL to one that already exists.
        """
        bookmark = await self.repository.get_by_id_with_relations(bookmark_id, user_id)
        if not bookmark:
            raise NotFoundError(
                resource="Bookmark",
                resource_id=bookmark_id,
                code=ErrorCode.BOOKMARK_NOT_FOUND,
            )

        # Check for duplicate URL if URL is being changed
        if data.url and data.url != bookmark.url:
            existing = await self.repository.get_by_url(data.url, user_id)
            if existing:
                raise ConflictError(
                    resource="Bookmark",
                    field="url",
                    value=data.url,
                )

        # Update scalar fields
        update_data = data.model_dump(
            exclude_unset=True,
            exclude={"tag_ids", "collection_ids"},
        )
        if update_data:
            bookmark = await self.repository.update(bookmark, **update_data)

        # Update relations if provided
        if data.tag_ids is not None or data.collection_ids is not None:
            bookmark = await self.repository.update_relations(
                bookmark,
                user_id,
                tag_ids=data.tag_ids,
                collection_ids=data.collection_ids,
            )

        return self._to_read_schema(bookmark)

    async def delete(
        self,
        bookmark_id: UUID,
        user_id: UUID,
    ) -> None:
        """Delete a bookmark.

        Args:
            bookmark_id: Bookmark's UUID.
            user_id: Owner's UUID for authorization.

        Raises:
            NotFoundError: If bookmark not found or not owned by user.
        """
        bookmark = await self.repository.get_by_id_with_relations(bookmark_id, user_id)
        if not bookmark:
            raise NotFoundError(
                resource="Bookmark",
                resource_id=bookmark_id,
                code=ErrorCode.BOOKMARK_NOT_FOUND,
            )

        await self.repository.delete(bookmark)

    async def refresh_metadata(
        self,
        bookmark_id: UUID,
        user_id: UUID,
    ) -> BookmarkRead:
        """Re-fetch metadata for a bookmark from its URL.

        Args:
            bookmark_id: Bookmark's UUID.
            user_id: Owner's UUID for authorization.

        Returns:
            Updated bookmark with refreshed metadata.

        Raises:
            NotFoundError: If bookmark not found or not owned by user.
        """
        bookmark = await self.repository.get_by_id_with_relations(bookmark_id, user_id)
        if not bookmark:
            raise NotFoundError(
                resource="Bookmark",
                resource_id=bookmark_id,
                code=ErrorCode.BOOKMARK_NOT_FOUND,
            )

        # Fetch metadata
        metadata = await fetch_url_metadata(bookmark.url)

        # Update bookmark with fetched metadata
        update_data: dict[str, str | None] = {}
        if metadata.title:
            update_data["title"] = metadata.title
        if metadata.description:
            update_data["description"] = metadata.description
        if metadata.favicon_url:
            update_data["favicon_url"] = metadata.favicon_url

        if update_data:
            bookmark = await self.repository.update(bookmark, **update_data)

        return self._to_read_schema(bookmark)

    def _to_read_schema(self, bookmark: Bookmark) -> BookmarkRead:
        """Convert bookmark model to read schema.

        Args:
            bookmark: Bookmark model instance.

        Returns:
            BookmarkRead schema.
        """
        return BookmarkRead.model_validate(bookmark)
