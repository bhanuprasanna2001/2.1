"""Tests for collection endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_collections_empty(client: AsyncClient) -> None:
    """Test listing collections when none exist."""
    response = await client.get("/api/v1/collections")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_collection(client: AsyncClient) -> None:
    """Test creating a new collection."""
    collection_data = {
        "name": "Development",
        "description": "Development resources",
        "color": "#3B82F6",
    }

    response = await client.post("/api/v1/collections", json=collection_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == collection_data["name"]
    assert data["description"] == collection_data["description"]
    assert data["color"] == collection_data["color"]
    assert data["bookmark_count"] == 0


@pytest.mark.asyncio
async def test_create_nested_collection(client: AsyncClient) -> None:
    """Test creating a nested collection."""
    # Create parent
    parent_response = await client.post(
        "/api/v1/collections",
        json={"name": "Parent Collection"},
    )
    parent_id = parent_response.json()["id"]

    # Create child
    response = await client.post(
        "/api/v1/collections",
        json={"name": "Child Collection", "parent_id": parent_id},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["parent_id"] == parent_id


@pytest.mark.asyncio
async def test_get_collection(client: AsyncClient) -> None:
    """Test getting a single collection."""
    create_response = await client.post(
        "/api/v1/collections",
        json={"name": "Get Test Collection"},
    )
    collection_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/collections/{collection_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == collection_id
    assert data["name"] == "Get Test Collection"


@pytest.mark.asyncio
async def test_update_collection(client: AsyncClient) -> None:
    """Test updating a collection."""
    create_response = await client.post(
        "/api/v1/collections",
        json={"name": "Original Name"},
    )
    collection_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/collections/{collection_id}",
        json={"name": "Updated Name", "color": "#10B981"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["color"] == "#10B981"


@pytest.mark.asyncio
async def test_delete_collection(client: AsyncClient) -> None:
    """Test deleting a collection."""
    create_response = await client.post(
        "/api/v1/collections",
        json={"name": "Delete Test"},
    )
    collection_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/collections/{collection_id}")
    assert response.status_code == 204

    get_response = await client.get(f"/api/v1/collections/{collection_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_list_root_collections_only(client: AsyncClient) -> None:
    """Test listing only root-level collections."""
    # Create parent
    parent_response = await client.post(
        "/api/v1/collections",
        json={"name": "Root Collection"},
    )
    parent_id = parent_response.json()["id"]

    # Create child
    await client.post(
        "/api/v1/collections",
        json={"name": "Child Collection", "parent_id": parent_id},
    )

    # List root only
    response = await client.get("/api/v1/collections?root_only=true")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Root Collection"


@pytest.mark.asyncio
async def test_create_collection_duplicate_name(client: AsyncClient) -> None:
    """Test that duplicate names are rejected."""
    await client.post(
        "/api/v1/collections",
        json={"name": "Duplicate Name"},
    )

    response = await client.post(
        "/api/v1/collections",
        json={"name": "Duplicate Name"},
    )

    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "DUPLICATE_RESOURCE"


@pytest.mark.asyncio
async def test_create_collection_invalid_color(client: AsyncClient) -> None:
    """Test that invalid color codes are rejected."""
    response = await client.post(
        "/api/v1/collections",
        json={"name": "Invalid Color", "color": "red"},
    )

    assert response.status_code == 422
