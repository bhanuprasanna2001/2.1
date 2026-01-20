"""Collection model for organizing bookmarks."""

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.bookmark import Bookmark
    from app.models.user import User


class Collection(Base, TimestampMixin):
    """Collection model for organizing bookmarks into folders.

    Supports hierarchical structure through parent_id self-reference.

    Attributes:
        id: Unique identifier (UUID).
        user_id: Owner of the collection.
        name: Collection name.
        description: Optional description.
        parent_id: Parent collection for nesting.
        color: Optional color for UI display.
        icon: Optional icon name.
        bookmarks: Bookmarks in this collection.
        children: Nested sub-collections.
    """

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )

    color: Mapped[str | None] = mapped_column(
        String(7),  # Hex color code (#RRGGBB)
        nullable=True,
    )

    icon: Mapped[str | None] = mapped_column(
        String(50),  # Icon name
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="collections",
    )

    bookmarks: Mapped[list["Bookmark"]] = relationship(
        "Bookmark",
        secondary="bookmark_collections",
        back_populates="collections",
        lazy="selectin",
    )

    # Self-referential relationship for hierarchy
    parent: Mapped["Collection | None"] = relationship(
        "Collection",
        back_populates="children",
        remote_side="Collection.id",
    )

    children: Mapped[list["Collection"]] = relationship(
        "Collection",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Collection {self.name}>"
