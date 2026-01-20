"""Collection schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


class CollectionBase(BaseSchema):
    """Base schema for collection data."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Collection name",
        examples=["Development Resources"],
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Collection description",
        examples=["Articles and documentation for software development"],
    )
    color: str | None = Field(
        default=None,
        description="Hex color code for UI display",
        examples=["#3B82F6"],
    )
    icon: str | None = Field(
        default=None,
        max_length=50,
        description="Icon name for UI display",
        examples=["folder", "star", "code"],
    )

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        """Validate hex color code format."""
        if v is not None:
            if not v.startswith("#") or len(v) != 7:
                msg = "Color must be a valid hex code (e.g., #3B82F6)"
                raise ValueError(msg)
            try:
                int(v[1:], 16)
            except ValueError:
                msg = "Color must be a valid hex code"
                raise ValueError(msg) from None
        return v


class CollectionCreate(CollectionBase):
    """Schema for creating a new collection."""

    parent_id: UUID | None = Field(
        default=None,
        description="Parent collection ID for nesting",
    )


class CollectionUpdate(BaseSchema):
    """Schema for updating an existing collection.

    All fields are optional - only provided fields will be updated.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    description: str | None = None
    color: str | None = None
    icon: str | None = None
    parent_id: UUID | None = None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        """Validate hex color code format if provided."""
        if v is not None and v != "":
            if not v.startswith("#") or len(v) != 7:
                msg = "Color must be a valid hex code (e.g., #3B82F6)"
                raise ValueError(msg)
            try:
                int(v[1:], 16)
            except ValueError:
                msg = "Color must be a valid hex code"
                raise ValueError(msg) from None
        return v


class CollectionSummary(BaseSchema):
    """Minimal collection representation."""

    id: UUID
    name: str
    color: str | None = None
    icon: str | None = None


class CollectionRead(CollectionBase):
    """Schema for reading collection data."""

    id: UUID
    user_id: UUID
    parent_id: UUID | None = None
    bookmark_count: int = Field(default=0, description="Number of bookmarks in collection")
    children: list["CollectionSummary"] = Field(
        default_factory=list,
        description="Child collections",
    )
    created_at: datetime
    updated_at: datetime


class CollectionTree(BaseSchema):
    """Collection with full nested children tree."""

    id: UUID
    user_id: UUID
    name: str
    description: str | None = None
    color: str | None = None
    icon: str | None = None
    parent_id: UUID | None = None
    bookmark_count: int = 0
    children: list["CollectionTree"] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
