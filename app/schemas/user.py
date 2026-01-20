"""User schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.schemas.base import BaseSchema


class UserBase(BaseSchema):
    """Base schema for user data."""

    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"],
    )
    display_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Display name shown in the UI",
        examples=["John Doe"],
    )


class UserCreate(UserBase):
    """Schema for user registration.

    Password requirements:
    - Minimum 8 characters
    - Maximum 128 characters
    """

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User's password (min 8 characters)",
        examples=["SecureP@ssw0rd!"],
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets minimum security requirements."""
        if len(v) < 8:
            msg = "Password must be at least 8 characters long"
            raise ValueError(msg)
        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not (has_letter and has_digit):
            msg = "Password must contain at least one letter and one number"
            raise ValueError(msg)
        return v


class UserUpdate(BaseSchema):
    """Schema for updating user profile.

    All fields are optional - only provided fields will be updated.
    """

    display_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )


class UserUpdatePassword(BaseSchema):
    """Schema for changing user password."""

    current_password: str = Field(
        ...,
        min_length=1,
        description="Current password for verification",
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password",
    )

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate new password meets minimum security requirements."""
        if len(v) < 8:
            msg = "Password must be at least 8 characters long"
            raise ValueError(msg)
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not (has_letter and has_digit):
            msg = "Password must contain at least one letter and one number"
            raise ValueError(msg)
        return v


class UserRead(UserBase):
    """Schema for reading user data (public profile)."""

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Computed fields for user statistics (optional)
    bookmark_count: int = Field(default=0, description="Total number of bookmarks")
    collection_count: int = Field(default=0, description="Total number of collections")
    tag_count: int = Field(default=0, description="Total number of tags")
