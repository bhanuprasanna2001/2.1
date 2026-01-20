"""Repository package for data access layer."""

from app.repositories.base import BaseRepository
from app.repositories.bookmark import BookmarkRepository
from app.repositories.collection import CollectionRepository
from app.repositories.tag import TagRepository
from app.repositories.user import UserRepository

__all__ = [
    "BaseRepository",
    "BookmarkRepository",
    "CollectionRepository",
    "TagRepository",
    "UserRepository",
]
