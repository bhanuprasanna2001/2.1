"""Bookmark schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, HttpUrl, field_validator

from app.schemas.base import BaseSchema


class TagSummary(BaseSchema):
    """Minimal tag representation for embedding in bookmark responses."""

    id: UUID
    name: str
    color: str | None = None


class CollectionSummary(BaseSchema):
    """Minimal collection representation for embedding in bookmark responses."""

    id: UUID
    name: str
    color: str | None = None


class BookmarkBase(BaseSchema):
    """Base schema for bookmark data."""

    url: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="URL to bookmark",
        examples=["https://example.com/article"],
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Title of the bookmark",
        examples=["Interesting Article About Python"],
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Description or notes",
        examples=["Great article explaining async/await patterns"],
    )
    is_favorite: bool = Field(
        default=False,
        description="Mark as favorite",
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that the URL is properly formatted."""
        # Pydantic's HttpUrl for validation, but store as string
        HttpUrl(v)
        return v


class BookmarkCreate(BookmarkBase):
    """Schema for creating a new bookmark."""

    tag_ids: list[UUID] = Field(
        default_factory=list,
        description="IDs of tags to assign",
    )
    collection_ids: list[UUID] = Field(
        default_factory=list,
        description="IDs of collections to add to",
    )


class BookmarkUpdate(BaseSchema):
    """Schema for updating an existing bookmark.

    All fields are optional - only provided fields will be updated.
    """

    url: str | None = Field(
        default=None,
        min_length=1,
        max_length=2048,
    )
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
    )
    description: str | None = None
    favicon_url: str | None = None
    is_favorite: bool | None = None
    tag_ids: list[UUID] | None = None
    collection_ids: list[UUID] | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        """Validate URL if provided."""
        if v is not None:
            HttpUrl(v)
        return v


class BookmarkRead(BookmarkBase):
    """Schema for reading bookmark data."""

    id: UUID
    user_id: UUID
    favicon_url: str | None = None
    tags: list[TagSummary] = Field(default_factory=list)
    collections: list[CollectionSummary] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
