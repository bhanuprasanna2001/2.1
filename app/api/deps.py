"""API dependencies for dependency injection."""

from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ErrorCode
from app.core.security import verify_access_token
from app.database import get_db
from app.schemas.base import PaginationParams
from app.services.auth import AuthService
from app.services.bookmark import BookmarkService
from app.services.collection import CollectionService
from app.services.tag import TagService
from app.services.user import UserService

# Type alias for database session dependency
DBSession = Annotated[AsyncSession, Depends(get_db)]

# HTTP Bearer security scheme
# auto_error=False allows us to handle missing tokens gracefully
bearer_scheme = HTTPBearer(auto_error=False)


async def get_bookmark_service(
    session: DBSession,
) -> AsyncGenerator[BookmarkService, None]:
    """Get bookmark service instance.

    Args:
        session: Database session.

    Yields:
        BookmarkService instance.
    """
    yield BookmarkService(session)


async def get_collection_service(
    session: DBSession,
) -> AsyncGenerator[CollectionService, None]:
    """Get collection service instance.

    Args:
        session: Database session.

    Yields:
        CollectionService instance.
    """
    yield CollectionService(session)


async def get_tag_service(
    session: DBSession,
) -> AsyncGenerator[TagService, None]:
    """Get tag service instance.

    Args:
        session: Database session.

    Yields:
        TagService instance.
    """
    yield TagService(session)


async def get_auth_service(
    session: DBSession,
) -> AsyncGenerator[AuthService, None]:
    """Get auth service instance.

    Args:
        session: Database session.

    Yields:
        AuthService instance.
    """
    yield AuthService(session)


async def get_user_service(
    session: DBSession,
) -> AsyncGenerator[UserService, None]:
    """Get user service instance.

    Args:
        session: Database session.

    Yields:
        UserService instance.
    """
    yield UserService(session)


def get_pagination(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> PaginationParams:
    """Get pagination parameters from query.

    Args:
        page: Page number (1-indexed).
        limit: Items per page.

    Returns:
        PaginationParams instance.
    """
    return PaginationParams(page=page, limit=limit)


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UUID:
    """Extract and verify user ID from JWT token.

    This dependency extracts the Bearer token from the Authorization header,
    verifies it, and returns the user ID.

    Args:
        credentials: HTTP Bearer credentials from Authorization header.

    Returns:
        User's UUID from the verified token.

    Raises:
        AuthenticationError: If token is missing, invalid, or expired.
    """
    if credentials is None:
        raise AuthenticationError(
            message="Authentication required",
            code=ErrorCode.UNAUTHORIZED,
        )

    user_id = verify_access_token(credentials.credentials)
    if user_id is None:
        raise AuthenticationError(
            message="Invalid or expired token",
            code=ErrorCode.TOKEN_INVALID,
        )

    return user_id


async def get_optional_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UUID | None:
    """Extract user ID from JWT token if present.

    This dependency is similar to get_current_user_id but doesn't raise
    an error if no token is provided. Useful for endpoints that support
    both authenticated and anonymous access.

    Args:
        credentials: HTTP Bearer credentials from Authorization header.

    Returns:
        User's UUID if token is valid, None otherwise.
    """
    if credentials is None:
        return None

    return verify_access_token(credentials.credentials)


# Type aliases for dependency injection
BookmarkServiceDep = Annotated[BookmarkService, Depends(get_bookmark_service)]
CollectionServiceDep = Annotated[CollectionService, Depends(get_collection_service)]
TagServiceDep = Annotated[TagService, Depends(get_tag_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
PaginationDep = Annotated[PaginationParams, Depends(get_pagination)]
CurrentUserID = Annotated[UUID, Depends(get_current_user_id)]
OptionalUserID = Annotated[UUID | None, Depends(get_optional_user_id)]
