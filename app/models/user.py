"""User model for authentication and ownership."""

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.bookmark import Bookmark
    from app.models.collection import Collection
    from app.models.tag import Tag


class User(Base, TimestampMixin):
    """User model for authentication and resource ownership.

    Attributes:
        id: Unique identifier (UUID).
        email: Unique email address.
        hashed_password: Argon2 hashed password.
        display_name: Optional display name.
        is_active: Whether the user account is active.
        bookmarks: User's bookmarks.
        collections: User's collections.
        tags: User's tags.
    """

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    email: Mapped[str] = mapped_column(
        String(320),  # Max email length per RFC 5321
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(128),  # Argon2 hash length
        nullable=False,
    )

    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    # Relationships
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        "Bookmark",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    collections: Mapped[list["Collection"]] = relationship(
        "Collection",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
