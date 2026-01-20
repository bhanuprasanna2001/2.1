"""Pydantic schemas package."""

from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.base import PaginatedResponse, PaginationParams
from app.schemas.bookmark import (
    BookmarkCreate,
    BookmarkRead,
    BookmarkUpdate,
)
from app.schemas.collection import (
    CollectionCreate,
    CollectionRead,
    CollectionUpdate,
)
from app.schemas.tag import (
    TagCreate,
    TagRead,
    TagUpdate,
)
from app.schemas.user import (
    UserCreate,
    UserRead,
    UserUpdate,
    UserUpdatePassword,
)

__all__ = [
    "AccessTokenResponse",
    "BookmarkCreate",
    "BookmarkRead",
    "BookmarkUpdate",
    "CollectionCreate",
    "CollectionRead",
    "CollectionUpdate",
    "LoginRequest",
    "PaginatedResponse",
    "PaginationParams",
    "RefreshRequest",
    "TagCreate",
    "TagRead",
    "TagUpdate",
    "TokenResponse",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "UserUpdatePassword",
]
