"""API v1 router aggregating all endpoints."""

from fastapi import APIRouter

from app.api.v1 import auth, bookmarks, collections, health, tags, users

api_router = APIRouter()

# Include all routers
api_router.include_router(
    health.router,
    prefix="",
    tags=["System"],
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
)

api_router.include_router(
    bookmarks.router,
    prefix="/bookmarks",
    tags=["Bookmarks"],
)

api_router.include_router(
    collections.router,
    prefix="/collections",
    tags=["Collections"],
)

api_router.include_router(
    tags.router,
    prefix="/tags",
    tags=["Tags"],
)
