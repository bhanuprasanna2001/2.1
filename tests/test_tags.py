"""Tests for tag endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_tags_empty(client: AsyncClient) -> None:
    """Test listing tags when none exist."""
    response = await client.get("/api/v1/tags")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_tag(client: AsyncClient) -> None:
    """Test creating a new tag."""
    tag_data = {
        "name": "Python",
        "color": "#3776AB",
    }

    response = await client.post("/api/v1/tags", json=tag_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "python"  # Normalized to lowercase
    assert data["color"] == tag_data["color"]
    assert data["bookmark_count"] == 0


@pytest.mark.asyncio
async def test_create_tag_normalized(client: AsyncClient) -> None:
    """Test that tag names are normalized to lowercase."""
    response = await client.post(
        "/api/v1/tags",
        json={"name": "  UPPERCASE TAG  "},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "uppercase tag"


@pytest.mark.asyncio
async def test_get_tag(client: AsyncClient) -> None:
    """Test getting a single tag."""
    create_response = await client.post(
        "/api/v1/tags",
        json={"name": "get-test"},
    )
    tag_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/tags/{tag_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tag_id
    assert data["name"] == "get-test"


@pytest.mark.asyncio
async def test_update_tag(client: AsyncClient) -> None:
    """Test updating a tag."""
    create_response = await client.post(
        "/api/v1/tags",
        json={"name": "original-tag"},
    )
    tag_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/tags/{tag_id}",
        json={"name": "updated-tag", "color": "#10B981"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated-tag"
    assert data["color"] == "#10B981"


@pytest.mark.asyncio
async def test_delete_tag(client: AsyncClient) -> None:
    """Test deleting a tag."""
    create_response = await client.post(
        "/api/v1/tags",
        json={"name": "delete-test"},
    )
    tag_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/tags/{tag_id}")
    assert response.status_code == 204

    get_response = await client.get(f"/api/v1/tags/{tag_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_create_tag_duplicate_name(client: AsyncClient) -> None:
    """Test that duplicate tag names are rejected."""
    await client.post("/api/v1/tags", json={"name": "duplicate"})

    response = await client.post("/api/v1/tags", json={"name": "duplicate"})

    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "DUPLICATE_RESOURCE"


@pytest.mark.asyncio
async def test_search_tags(client: AsyncClient) -> None:
    """Test searching tags by name."""
    # Create multiple tags
    await client.post("/api/v1/tags", json={"name": "python"})
    await client.post("/api/v1/tags", json={"name": "javascript"})
    await client.post("/api/v1/tags", json={"name": "typescript"})

    # Search for "script"
    response = await client.get("/api/v1/tags?search=script")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    names = [t["name"] for t in data["items"]]
    assert "javascript" in names
    assert "typescript" in names


@pytest.mark.asyncio
async def test_create_tag_invalid_color(client: AsyncClient) -> None:
    """Test that invalid color codes are rejected."""
    response = await client.post(
        "/api/v1/tags",
        json={"name": "invalid-color", "color": "blue"},
    )

    assert response.status_code == 422
