"""Bookmark endpoints."""

from enum import StrEnum
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import BookmarkServiceDep, CurrentUserID, PaginationDep
from app.schemas.base import PaginatedResponse
from app.schemas.bookmark import BookmarkCreate, BookmarkRead, BookmarkUpdate


class SortBy(StrEnum):
    """Available sort fields for bookmarks."""

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    TITLE = "title"


class SortOrder(StrEnum):
    """Sort order options."""

    ASC = "asc"
    DESC = "desc"


router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[BookmarkRead],
    summary="List bookmarks",
    description="Get a paginated list of bookmarks for the current user with optional filtering and sorting.",
)
async def list_bookmarks(
    service: BookmarkServiceDep,
    user_id: CurrentUserID,
    pagination: PaginationDep,
    is_favorite: Annotated[
        bool | None,
        Query(description="Filter by favorite status"),
    ] = None,
    tag_id: Annotated[
        UUID | None,
        Query(description="Filter by tag ID"),
    ] = None,
    collection_id: Annotated[
        UUID | None,
        Query(description="Filter by collection ID"),
    ] = None,
    search: Annotated[
        str | None,
        Query(max_length=100, description="Search in title and description"),
    ] = None,
    sort_by: Annotated[
        SortBy,
        Query(description="Field to sort by"),
    ] = SortBy.CREATED_AT,
    sort_order: Annotated[
        SortOrder,
        Query(description="Sort direction"),
    ] = SortOrder.DESC,
) -> PaginatedResponse[BookmarkRead]:
    """List bookmarks with optional filtering and sorting.

    - **is_favorite**: Filter by favorite status (true/false)
    - **tag_id**: Filter by tag
    - **collection_id**: Filter by collection
    - **search**: Search in title and description
    - **sort_by**: Field to sort by (created_at, updated_at, title)
    - **sort_order**: Sort direction (asc, desc)
    """
    return await service.list(
        user_id,
        page=pagination.page,
        limit=pagination.limit,
        is_favorite=is_favorite,
        tag_id=tag_id,
        collection_id=collection_id,
        search=search,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
    )


@router.post(
    "",
    response_model=BookmarkRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create bookmark",
    description="Create a new bookmark with optional tags and collections.",
)
async def create_bookmark(
    data: BookmarkCreate,
    service: BookmarkServiceDep,
    user_id: CurrentUserID,
    auto_fetch_metadata: Annotated[
        bool | None,
        Query(description="Auto-fetch title, description, and favicon from URL"),
    ] = None,
) -> BookmarkRead:
    """Create a new bookmark.

    - **url**: The URL to bookmark (required)
    - **title**: Title for the bookmark (required)
    - **description**: Optional description or notes
    - **is_favorite**: Mark as favorite (default: false)
    - **tag_ids**: List of tag IDs to assign
    - **collection_ids**: List of collection IDs to add to
    - **auto_fetch_metadata**: Override default setting for auto-fetching metadata
    """
    return await service.create(user_id, data, auto_fetch_metadata=auto_fetch_metadata)


@router.get(
    "/{bookmark_id}",
    response_model=BookmarkRead,
    summary="Get bookmark",
    description="Get a bookmark by its ID.",
)
async def get_bookmark(
    bookmark_id: UUID,
    service: BookmarkServiceDep,
    user_id: CurrentUserID,
) -> BookmarkRead:
    """Get a specific bookmark by ID."""
    return await service.get_by_id(bookmark_id, user_id)


@router.patch(
    "/{bookmark_id}",
    response_model=BookmarkRead,
    summary="Update bookmark",
    description="Update a bookmark. Only provided fields will be updated.",
)
async def update_bookmark(
    bookmark_id: UUID,
    data: BookmarkUpdate,
    service: BookmarkServiceDep,
    user_id: CurrentUserID,
) -> BookmarkRead:
    """Update a bookmark.

    Only fields included in the request body will be updated.
    To update tags or collections, provide the complete list of IDs.
    """
    return await service.update(bookmark_id, user_id, data)


@router.delete(
    "/{bookmark_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete bookmark",
    description="Delete a bookmark permanently.",
)
async def delete_bookmark(
    bookmark_id: UUID,
    service: BookmarkServiceDep,
    user_id: CurrentUserID,
) -> None:
    """Delete a bookmark.

    This action is permanent and cannot be undone.
    """
    await service.delete(bookmark_id, user_id)


@router.post(
    "/{bookmark_id}/refresh-metadata",
    response_model=BookmarkRead,
    summary="Refresh bookmark metadata",
    description="Re-fetch title, description, and favicon from the bookmark's URL.",
)
async def refresh_bookmark_metadata(
    bookmark_id: UUID,
    service: BookmarkServiceDep,
    user_id: CurrentUserID,
) -> BookmarkRead:
    """Refresh metadata for a bookmark.

    Fetches the current title, description, and favicon from the URL
    and updates the bookmark accordingly.
    """
    return await service.refresh_metadata(bookmark_id, user_id)
