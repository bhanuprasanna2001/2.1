"""Bookmark model and association tables."""

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.collection import Collection
    from app.models.tag import Tag
    from app.models.user import User


# Association table for Bookmark <-> Tag (many-to-many)
BookmarkTag = Table(
    "bookmark_tags",
    Base.metadata,
    Column(
        "bookmark_id",
        ForeignKey("bookmarks.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# Association table for Bookmark <-> Collection (many-to-many)
BookmarkCollection = Table(
    "bookmark_collections",
    Base.metadata,
    Column(
        "bookmark_id",
        ForeignKey("bookmarks.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "collection_id",
        ForeignKey("collections.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Bookmark(Base, TimestampMixin):
    """Bookmark model representing a saved URL.

    Attributes:
        id: Unique identifier (UUID).
        user_id: Owner of the bookmark.
        url: The bookmarked URL.
        title: Title of the page (auto-fetched or user-provided).
        description: Description or notes.
        favicon_url: URL to the site's favicon.
        is_favorite: Whether marked as favorite.
        tags: Associated tags.
        collections: Collections containing this bookmark.
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

    url: Mapped[str] = mapped_column(
        String(2048),  # Max URL length
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    favicon_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    is_favorite: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="bookmarks",
    )

    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary=BookmarkTag,
        back_populates="bookmarks",
        lazy="selectin",
    )

    collections: Mapped[list["Collection"]] = relationship(
        "Collection",
        secondary=BookmarkCollection,
        back_populates="bookmarks",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Bookmark {self.title[:30]}>"
