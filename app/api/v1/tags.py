"""Tag endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUserID, PaginationDep, TagServiceDep
from app.schemas.base import PaginatedResponse
from app.schemas.tag import TagCreate, TagRead, TagUpdate

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[TagRead],
    summary="List tags",
    description="Get a paginated list of tags for the current user.",
)
async def list_tags(
    service: TagServiceDep,
    user_id: CurrentUserID,
    pagination: PaginationDep,
    search: Annotated[
        str | None,
        Query(max_length=50, description="Search in tag name"),
    ] = None,
) -> PaginatedResponse[TagRead]:
    """List tags with optional search.

    - **search**: Filter tags by name (partial match)

    Tags are returned with their usage count (number of bookmarks).
    """
    return await service.list(
        user_id,
        page=pagination.page,
        limit=pagination.limit,
        search=search,
    )


@router.post(
    "",
    response_model=TagRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create tag",
    description="Create a new tag for categorizing bookmarks.",
)
async def create_tag(
    data: TagCreate,
    service: TagServiceDep,
    user_id: CurrentUserID,
) -> TagRead:
    """Create a new tag.

    - **name**: Tag name (required, will be normalized to lowercase)
    - **color**: Hex color code (e.g., #10B981)

    Tag names are unique per user.
    """
    return await service.create(user_id, data)


@router.get(
    "/{tag_id}",
    response_model=TagRead,
    summary="Get tag",
    description="Get a tag by its ID.",
)
async def get_tag(
    tag_id: UUID,
    service: TagServiceDep,
    user_id: CurrentUserID,
) -> TagRead:
    """Get a specific tag by ID.

    Returns the tag with its usage count (number of bookmarks).
    """
    return await service.get_by_id(tag_id, user_id)


@router.patch(
    "/{tag_id}",
    response_model=TagRead,
    summary="Update tag",
    description="Update a tag. Only provided fields will be updated.",
)
async def update_tag(
    tag_id: UUID,
    data: TagUpdate,
    service: TagServiceDep,
    user_id: CurrentUserID,
) -> TagRead:
    """Update a tag.

    Only fields included in the request body will be updated.
    """
    return await service.update(tag_id, user_id, data)


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tag",
    description="Delete a tag. Bookmarks with this tag will be untagged.",
)
async def delete_tag(
    tag_id: UUID,
    service: TagServiceDep,
    user_id: CurrentUserID,
) -> None:
    """Delete a tag.

    Bookmarks that have this tag will have it removed.
    The bookmarks themselves are NOT deleted.
    """
    await service.delete(tag_id, user_id)
