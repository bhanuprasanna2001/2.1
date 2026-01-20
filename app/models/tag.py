"""Tag model for categorizing bookmarks."""

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.bookmark import Bookmark
    from app.models.user import User


class Tag(Base, TimestampMixin):
    """Tag model for categorizing bookmarks.

    Tags are user-scoped, meaning each user has their own set of tags.
    The same tag name can exist for different users.

    Attributes:
        id: Unique identifier (UUID).
        user_id: Owner of the tag.
        name: Tag name (unique per user).
        color: Optional color for UI display.
        bookmarks: Bookmarks with this tag.
    """

    __table_args__ = (
        # Ensure tag names are unique per user
        UniqueConstraint("user_id", "name", name="uq_tag_user_name"),
    )

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
        String(50),
        nullable=False,
        index=True,
    )

    color: Mapped[str | None] = mapped_column(
        String(7),  # Hex color code (#RRGGBB)
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="tags",
    )

    bookmarks: Mapped[list["Bookmark"]] = relationship(
        "Bookmark",
        secondary="bookmark_tags",
        back_populates="tags",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"
