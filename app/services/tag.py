"""Tag service for business logic."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ErrorCode, NotFoundError
from app.models.tag import Tag
from app.repositories.tag import TagRepository
from app.schemas.base import PaginatedResponse
from app.schemas.tag import TagCreate, TagRead, TagUpdate


class TagService:
    """Service for tag business logic.

    Handles operations on tags including validation and
    authorization checks.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service with database session.

        Args:
            session: Async database session.
        """
        self.session = session
        self.repository = TagRepository(session)

    async def create(
        self,
        user_id: UUID,
        data: TagCreate,
    ) -> TagRead:
        """Create a new tag.

        Args:
            user_id: Owner's UUID.
            data: Tag creation data.

        Returns:
            Created tag.

        Raises:
            ConflictError: If tag name already exists for user.
        """
        # Check for duplicate name (names are normalized to lowercase)
        existing = await self.repository.get_by_name(data.name, user_id)
        if existing:
            raise ConflictError(
                resource="Tag",
                field="name",
                value=data.name,
            )

        tag = await self.repository.create(
            user_id=user_id,
            name=data.name,  # Already normalized by schema
            color=data.color,
        )

        return await self._to_read_schema(tag)

    async def get_by_id(
        self,
        tag_id: UUID,
        user_id: UUID,
    ) -> TagRead:
        """Get a tag by ID.

        Args:
            tag_id: Tag's UUID.
            user_id: Owner's UUID for authorization.

        Returns:
            Tag data.

        Raises:
            NotFoundError: If tag not found or not owned by user.
        """
        tag = await self.repository.get_by_id_for_user(tag_id, user_id)
        if not tag:
            raise NotFoundError(
                resource="Tag",
                resource_id=tag_id,
                code=ErrorCode.TAG_NOT_FOUND,
            )
        return await self._to_read_schema(tag)

    async def list(
        self,
        user_id: UUID,
        *,
        page: int = 1,
        limit: int = 50,
        search: str | None = None,
    ) -> PaginatedResponse[TagRead]:
        """List tags for a user.

        Args:
            user_id: Owner's UUID.
            page: Page number (1-indexed).
            limit: Items per page.
            search: Search in tag name.

        Returns:
            Paginated list of tags.
        """
        offset = (page - 1) * limit

        tags = await self.repository.get_by_user(
            user_id,
            offset=offset,
            limit=limit,
            search=search,
        )

        total = await self.repository.count_by_user(
            user_id,
            search=search,
        )

        items = [await self._to_read_schema(t) for t in tags]

        return PaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            limit=limit,
        )

    async def update(
        self,
        tag_id: UUID,
        user_id: UUID,
        data: TagUpdate,
    ) -> TagRead:
        """Update a tag.

        Args:
            tag_id: Tag's UUID.
            user_id: Owner's UUID for authorization.
            data: Update data.

        Returns:
            Updated tag.

        Raises:
            NotFoundError: If tag not found.
            ConflictError: If updating name to one that already exists.
        """
        tag = await self.repository.get_by_id_for_user(tag_id, user_id)
        if not tag:
            raise NotFoundError(
                resource="Tag",
                resource_id=tag_id,
                code=ErrorCode.TAG_NOT_FOUND,
            )

        # Check for duplicate name if name is being changed
        if data.name and data.name != tag.name:
            existing = await self.repository.get_by_name(data.name, user_id)
            if existing:
                raise ConflictError(
                    resource="Tag",
                    field="name",
                    value=data.name,
                )

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            tag = await self.repository.update(tag, **update_data)

        return await self._to_read_schema(tag)

    async def delete(
        self,
        tag_id: UUID,
        user_id: UUID,
    ) -> None:
        """Delete a tag.

        Note: This will remove the tag from all bookmarks.

        Args:
            tag_id: Tag's UUID.
            user_id: Owner's UUID for authorization.

        Raises:
            NotFoundError: If tag not found.
        """
        tag = await self.repository.get_by_id_for_user(tag_id, user_id)
        if not tag:
            raise NotFoundError(
                resource="Tag",
                resource_id=tag_id,
                code=ErrorCode.TAG_NOT_FOUND,
            )

        await self.repository.delete(tag)

    async def _to_read_schema(self, tag: Tag) -> TagRead:
        """Convert tag model to read schema.

        Args:
            tag: Tag model instance.

        Returns:
            TagRead schema with bookmark count.
        """
        bookmark_count = await self.repository.get_bookmark_count(tag.id)

        return TagRead(
            id=tag.id,
            user_id=tag.user_id,
            name=tag.name,
            color=tag.color,
            bookmark_count=bookmark_count,
            created_at=tag.created_at,
            updated_at=tag.updated_at,
        )
