"""Collection endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import CollectionServiceDep, CurrentUserID, PaginationDep
from app.schemas.base import PaginatedResponse
from app.schemas.collection import CollectionCreate, CollectionRead, CollectionUpdate

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[CollectionRead],
    summary="List collections",
    description="Get a paginated list of collections for the current user.",
)
async def list_collections(
    service: CollectionServiceDep,
    user_id: CurrentUserID,
    pagination: PaginationDep,
    parent_id: Annotated[
        UUID | None,
        Query(description="Filter by parent collection ID"),
    ] = None,
    root_only: Annotated[
        bool,
        Query(description="Only return root-level collections (no parent)"),
    ] = False,
) -> PaginatedResponse[CollectionRead]:
    """List collections with optional filtering.

    - **parent_id**: Filter by parent collection
    - **root_only**: Only return root-level collections (no parent)
    """
    return await service.list(
        user_id,
        page=pagination.page,
        limit=pagination.limit,
        parent_id=parent_id,
        root_only=root_only,
    )


@router.post(
    "",
    response_model=CollectionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create collection",
    description="Create a new collection (folder) for organizing bookmarks.",
)
async def create_collection(
    data: CollectionCreate,
    service: CollectionServiceDep,
    user_id: CurrentUserID,
) -> CollectionRead:
    """Create a new collection.

    - **name**: Collection name (required)
    - **description**: Optional description
    - **color**: Hex color code (e.g., #3B82F6)
    - **icon**: Icon name for UI display
    - **parent_id**: Parent collection ID for nesting
    """
    return await service.create(user_id, data)


@router.get(
    "/{collection_id}",
    response_model=CollectionRead,
    summary="Get collection",
    description="Get a collection by its ID.",
)
async def get_collection(
    collection_id: UUID,
    service: CollectionServiceDep,
    user_id: CurrentUserID,
) -> CollectionRead:
    """Get a specific collection by ID.

    Returns the collection with its children and bookmark count.
    """
    return await service.get_by_id(collection_id, user_id)


@router.patch(
    "/{collection_id}",
    response_model=CollectionRead,
    summary="Update collection",
    description="Update a collection. Only provided fields will be updated.",
)
async def update_collection(
    collection_id: UUID,
    data: CollectionUpdate,
    service: CollectionServiceDep,
    user_id: CurrentUserID,
) -> CollectionRead:
    """Update a collection.

    Only fields included in the request body will be updated.
    Changing parent_id moves the collection in the hierarchy.
    """
    return await service.update(collection_id, user_id, data)


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete collection",
    description="Delete a collection and all its sub-collections.",
)
async def delete_collection(
    collection_id: UUID,
    service: CollectionServiceDep,
    user_id: CurrentUserID,
) -> None:
    """Delete a collection.

    **Warning**: This also deletes all nested sub-collections.
    Bookmarks in the collection are NOT deleted, only unlinked.
    """
    await service.delete(collection_id, user_id)


# ─────────────────────────────────────────────────────────────────────────────
# Collection Bookmark Management Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/{collection_id}/bookmarks/{bookmark_id}",
    response_model=CollectionRead,
    status_code=status.HTTP_200_OK,
    summary="Add bookmark to collection",
    description="Add an existing bookmark to a collection.",
)
async def add_bookmark_to_collection(
    collection_id: UUID,
    bookmark_id: UUID,
    service: CollectionServiceDep,
    user_id: CurrentUserID,
) -> CollectionRead:
    """Add a bookmark to a collection.

    The bookmark and collection must both belong to the current user.
    A bookmark can belong to multiple collections.
    """
    return await service.add_bookmark(collection_id, bookmark_id, user_id)


@router.delete(
    "/{collection_id}/bookmarks/{bookmark_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove bookmark from collection",
    description="Remove a bookmark from a collection without deleting it.",
)
async def remove_bookmark_from_collection(
    collection_id: UUID,
    bookmark_id: UUID,
    service: CollectionServiceDep,
    user_id: CurrentUserID,
) -> None:
    """Remove a bookmark from a collection.

    This only removes the association, the bookmark itself is not deleted.
    """
    await service.remove_bookmark(collection_id, bookmark_id, user_id)
