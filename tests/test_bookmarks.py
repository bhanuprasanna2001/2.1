"""Tests for bookmark endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_bookmarks_empty(client: AsyncClient) -> None:
    """Test listing bookmarks when none exist."""
    response = await client.get("/api/v1/bookmarks")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_create_bookmark(client: AsyncClient) -> None:
    """Test creating a new bookmark."""
    bookmark_data = {
        "url": "https://example.com",
        "title": "Example Site",
        "description": "A test bookmark",
    }

    response = await client.post("/api/v1/bookmarks", json=bookmark_data)

    assert response.status_code == 201
    data = response.json()
    assert data["url"] == bookmark_data["url"]
    assert data["title"] == bookmark_data["title"]
    assert data["description"] == bookmark_data["description"]
    assert data["is_favorite"] is False
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_bookmark_duplicate_url(client: AsyncClient) -> None:
    """Test that duplicate URLs are rejected."""
    bookmark_data = {
        "url": "https://duplicate.com",
        "title": "First Bookmark",
    }

    # Create first bookmark
    response = await client.post("/api/v1/bookmarks", json=bookmark_data)
    assert response.status_code == 201

    # Try to create duplicate
    bookmark_data["title"] = "Second Bookmark"
    response = await client.post("/api/v1/bookmarks", json=bookmark_data)

    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "DUPLICATE_RESOURCE"


@pytest.mark.asyncio
async def test_get_bookmark(client: AsyncClient) -> None:
    """Test getting a single bookmark."""
    # Create a bookmark first
    create_response = await client.post(
        "/api/v1/bookmarks",
        json={"url": "https://get-test.com", "title": "Get Test"},
    )
    bookmark_id = create_response.json()["id"]

    # Get the bookmark
    response = await client.get(f"/api/v1/bookmarks/{bookmark_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == bookmark_id
    assert data["url"] == "https://get-test.com"


@pytest.mark.asyncio
async def test_get_bookmark_not_found(client: AsyncClient) -> None:
    """Test getting a non-existent bookmark."""
    fake_id = "00000000-0000-0000-0000-000000000099"
    response = await client.get(f"/api/v1/bookmarks/{fake_id}")

    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "BOOKMARK_NOT_FOUND"


@pytest.mark.asyncio
async def test_update_bookmark(client: AsyncClient) -> None:
    """Test updating a bookmark."""
    # Create a bookmark first
    create_response = await client.post(
        "/api/v1/bookmarks",
        json={"url": "https://update-test.com", "title": "Original Title"},
    )
    bookmark_id = create_response.json()["id"]

    # Update the bookmark
    response = await client.patch(
        f"/api/v1/bookmarks/{bookmark_id}",
        json={"title": "Updated Title", "is_favorite": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["is_favorite"] is True
    assert data["url"] == "https://update-test.com"  # Unchanged


@pytest.mark.asyncio
async def test_delete_bookmark(client: AsyncClient) -> None:
    """Test deleting a bookmark."""
    # Create a bookmark first
    create_response = await client.post(
        "/api/v1/bookmarks",
        json={"url": "https://delete-test.com", "title": "Delete Test"},
    )
    bookmark_id = create_response.json()["id"]

    # Delete the bookmark
    response = await client.delete(f"/api/v1/bookmarks/{bookmark_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(f"/api/v1/bookmarks/{bookmark_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_list_bookmarks_with_pagination(client: AsyncClient) -> None:
    """Test bookmark listing with pagination."""
    # Create multiple bookmarks
    for i in range(5):
        await client.post(
            "/api/v1/bookmarks",
            json={"url": f"https://page-test-{i}.com", "title": f"Bookmark {i}"},
        )

    # Get first page with limit of 2
    response = await client.get("/api/v1/bookmarks?page=1&limit=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["pages"] == 3


@pytest.mark.asyncio
async def test_create_bookmark_invalid_url(client: AsyncClient) -> None:
    """Test that invalid URLs are rejected."""
    response = await client.post(
        "/api/v1/bookmarks",
        json={"url": "not-a-valid-url", "title": "Invalid URL Test"},
    )

    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
