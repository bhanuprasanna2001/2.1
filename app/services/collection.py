"""Collection service for business logic."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ErrorCode, NotFoundError, ValidationError
from app.models.collection import Collection
from app.repositories.collection import CollectionRepository
from app.schemas.base import PaginatedResponse
from app.schemas.collection import (
    CollectionCreate,
    CollectionRead,
    CollectionSummary,
    CollectionUpdate,
)


class CollectionService:
    """Service for collection business logic.

    Handles operations on collections including validation,
    authorization checks, and hierarchy management.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service with database session.

        Args:
            session: Async database session.
        """
        self.session = session
        self.repository = CollectionRepository(session)

    async def create(
        self,
        user_id: UUID,
        data: CollectionCreate,
    ) -> CollectionRead:
        """Create a new collection.

        Args:
            user_id: Owner's UUID.
            data: Collection creation data.

        Returns:
            Created collection.

        Raises:
            ConflictError: If collection name already exists for user.
            NotFoundError: If parent collection not found.
        """
        # Check for duplicate name
        existing = await self.repository.get_by_name(data.name, user_id)
        if existing:
            raise ConflictError(
                resource="Collection",
                field="name",
                value=data.name,
            )

        # Validate parent exists if provided
        if data.parent_id:
            parent = await self.repository.get_by_id_with_relations(data.parent_id, user_id)
            if not parent:
                raise NotFoundError(
                    resource="Parent collection",
                    resource_id=data.parent_id,
                    code=ErrorCode.COLLECTION_NOT_FOUND,
                )

        collection = await self.repository.create(
            user_id=user_id,
            name=data.name,
            description=data.description,
            color=data.color,
            icon=data.icon,
            parent_id=data.parent_id,
        )

        return await self._to_read_schema(collection)

    async def get_by_id(
        self,
        collection_id: UUID,
        user_id: UUID,
    ) -> CollectionRead:
        """Get a collection by ID.

        Args:
            collection_id: Collection's UUID.
            user_id: Owner's UUID for authorization.

        Returns:
            Collection data.

        Raises:
            NotFoundError: If collection not found or not owned by user.
        """
        collection = await self.repository.get_by_id_with_relations(collection_id, user_id)
        if not collection:
            raise NotFoundError(
                resource="Collection",
                resource_id=collection_id,
                code=ErrorCode.COLLECTION_NOT_FOUND,
            )
        return await self._to_read_schema(collection)

    async def list(
        self,
        user_id: UUID,
        *,
        page: int = 1,
        limit: int = 50,
        parent_id: UUID | None = None,
        root_only: bool = False,
    ) -> PaginatedResponse[CollectionRead]:
        """List collections for a user.

        Args:
            user_id: Owner's UUID.
            page: Page number (1-indexed).
            limit: Items per page.
            parent_id: Filter by parent collection.
            root_only: Only return root-level collections.

        Returns:
            Paginated list of collections.
        """
        offset = (page - 1) * limit

        collections = await self.repository.get_by_user(
            user_id,
            offset=offset,
            limit=limit,
            parent_id=parent_id,
            root_only=root_only,
        )

        total = await self.repository.count_by_user(
            user_id,
            parent_id=parent_id,
            root_only=root_only,
        )

        items = [await self._to_read_schema(c) for c in collections]

        return PaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            limit=limit,
        )

    async def update(
        self,
        collection_id: UUID,
        user_id: UUID,
        data: CollectionUpdate,
    ) -> CollectionRead:
        """Update a collection.

        Args:
            collection_id: Collection's UUID.
            user_id: Owner's UUID for authorization.
            data: Update data.

        Returns:
            Updated collection.

        Raises:
            NotFoundError: If collection not found.
            ConflictError: If updating name to one that already exists.
            ValidationError: If parent_id would create a cycle.
        """
        collection = await self.repository.get_by_id_with_relations(collection_id, user_id)
        if not collection:
            raise NotFoundError(
                resource="Collection",
                resource_id=collection_id,
                code=ErrorCode.COLLECTION_NOT_FOUND,
            )

        # Check for duplicate name if name is being changed
        if data.name and data.name != collection.name:
            existing = await self.repository.get_by_name(data.name, user_id)
            if existing:
                raise ConflictError(
                    resource="Collection",
                    field="name",
                    value=data.name,
                )

        # Validate parent_id if being changed
        if data.parent_id is not None and data.parent_id != collection.parent_id:
            # Validate parent exists
            parent = await self.repository.get_by_id_with_relations(data.parent_id, user_id)
            if not parent:
                raise NotFoundError(
                    resource="Parent collection",
                    resource_id=data.parent_id,
                    code=ErrorCode.COLLECTION_NOT_FOUND,
                )

            # Check for cycles
            is_valid = await self.repository.is_valid_parent(collection_id, data.parent_id, user_id)
            if not is_valid:
                raise ValidationError(
                    message="Cannot set parent: would create a circular reference",
                    details=[{"field": "parent_id", "message": "Would create circular reference"}],
                )

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            collection = await self.repository.update(collection, **update_data)

        return await self._to_read_schema(collection)

    async def delete(
        self,
        collection_id: UUID,
        user_id: UUID,
    ) -> None:
        """Delete a collection.

        Note: This will also delete all child collections due to cascade.

        Args:
            collection_id: Collection's UUID.
            user_id: Owner's UUID for authorization.

        Raises:
            NotFoundError: If collection not found.
        """
        collection = await self.repository.get_by_id_with_relations(collection_id, user_id)
        if not collection:
            raise NotFoundError(
                resource="Collection",
                resource_id=collection_id,
                code=ErrorCode.COLLECTION_NOT_FOUND,
            )

        await self.repository.delete(collection)

    async def add_bookmark(
        self,
        collection_id: UUID,
        bookmark_id: UUID,
        user_id: UUID,
    ) -> CollectionRead:
        """Add a bookmark to a collection.

        Args:
            collection_id: Collection's UUID.
            bookmark_id: Bookmark's UUID to add.
            user_id: Owner's UUID for authorization.

        Returns:
            Updated collection.

        Raises:
            NotFoundError: If collection or bookmark not found.
            ConflictError: If bookmark is already in collection.
        """
        from app.repositories.bookmark import BookmarkRepository

        # Verify collection exists and belongs to user
        collection = await self.repository.get_by_id_with_relations(collection_id, user_id)
        if not collection:
            raise NotFoundError(
                resource="Collection",
                resource_id=collection_id,
                code=ErrorCode.COLLECTION_NOT_FOUND,
            )

        # Verify bookmark exists and belongs to user
        bookmark_repo = BookmarkRepository(self.session)
        bookmark = await bookmark_repo.get_by_id_with_relations(bookmark_id, user_id)
        if not bookmark:
            raise NotFoundError(
                resource="Bookmark",
                resource_id=bookmark_id,
                code=ErrorCode.BOOKMARK_NOT_FOUND,
            )

        # Check if bookmark is already in collection
        if collection in bookmark.collections:
            raise ConflictError(
                resource="Bookmark",
                field="collection",
                value=str(collection_id),
            )

        # Add bookmark to collection
        bookmark.collections.append(collection)
        await self.session.flush()

        return await self._to_read_schema(collection)

    async def remove_bookmark(
        self,
        collection_id: UUID,
        bookmark_id: UUID,
        user_id: UUID,
    ) -> None:
        """Remove a bookmark from a collection.

        Args:
            collection_id: Collection's UUID.
            bookmark_id: Bookmark's UUID to remove.
            user_id: Owner's UUID for authorization.

        Raises:
            NotFoundError: If collection or bookmark not found, or bookmark
                is not in the collection.
        """
        from app.repositories.bookmark import BookmarkRepository

        # Verify collection exists and belongs to user
        collection = await self.repository.get_by_id_with_relations(collection_id, user_id)
        if not collection:
            raise NotFoundError(
                resource="Collection",
                resource_id=collection_id,
                code=ErrorCode.COLLECTION_NOT_FOUND,
            )

        # Verify bookmark exists and belongs to user
        bookmark_repo = BookmarkRepository(self.session)
        bookmark = await bookmark_repo.get_by_id_with_relations(bookmark_id, user_id)
        if not bookmark:
            raise NotFoundError(
                resource="Bookmark",
                resource_id=bookmark_id,
                code=ErrorCode.BOOKMARK_NOT_FOUND,
            )

        # Check if bookmark is in collection
        if collection not in bookmark.collections:
            raise NotFoundError(
                resource="Bookmark in collection",
                resource_id=bookmark_id,
                code=ErrorCode.BOOKMARK_NOT_FOUND,
            )

        # Remove bookmark from collection
        bookmark.collections.remove(collection)
        await self.session.flush()

    async def _to_read_schema(self, collection: Collection) -> CollectionRead:
        """Convert collection model to read schema.

        Args:
            collection: Collection model instance.

        Returns:
            CollectionRead schema with bookmark count.
        """
        bookmark_count = await self.repository.get_bookmark_count(collection.id)

        return CollectionRead(
            id=collection.id,
            user_id=collection.user_id,
            name=collection.name,
            description=collection.description,
            color=collection.color,
            icon=collection.icon,
            parent_id=collection.parent_id,
            bookmark_count=bookmark_count,
            children=[
                CollectionSummary(
                    id=child.id,
                    name=child.name,
                    color=child.color,
                    icon=child.icon,
                )
                for child in collection.children
            ],
            created_at=collection.created_at,
            updated_at=collection.updated_at,
        )
