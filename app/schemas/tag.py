"""Tag schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


class TagBase(BaseSchema):
    """Base schema for tag data."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Tag name",
        examples=["python", "tutorial", "reference"],
    )
    color: str | None = Field(
        default=None,
        description="Hex color code for UI display",
        examples=["#10B981"],
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Normalize tag name (lowercase, stripped)."""
        return v.lower().strip()

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        """Validate hex color code format."""
        if v is not None:
            if not v.startswith("#") or len(v) != 7:
                msg = "Color must be a valid hex code (e.g., #10B981)"
                raise ValueError(msg)
            try:
                int(v[1:], 16)
            except ValueError:
                msg = "Color must be a valid hex code"
                raise ValueError(msg) from None
        return v


class TagCreate(TagBase):
    """Schema for creating a new tag."""

    pass


class TagUpdate(BaseSchema):
    """Schema for updating an existing tag.

    All fields are optional - only provided fields will be updated.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    color: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Normalize tag name if provided."""
        if v is not None:
            return v.lower().strip()
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        """Validate hex color code format if provided."""
        if v is not None and v != "":
            if not v.startswith("#") or len(v) != 7:
                msg = "Color must be a valid hex code (e.g., #10B981)"
                raise ValueError(msg)
            try:
                int(v[1:], 16)
            except ValueError:
                msg = "Color must be a valid hex code"
                raise ValueError(msg) from None
        return v


class TagRead(TagBase):
    """Schema for reading tag data."""

    id: UUID
    user_id: UUID
    bookmark_count: int = Field(default=0, description="Number of bookmarks with this tag")
    created_at: datetime
    updated_at: datetime
