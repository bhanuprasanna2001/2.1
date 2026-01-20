"""Health check and system endpoints."""

from fastapi import APIRouter

from app import __version__
from app.config import settings

router = APIRouter()


@router.get("/version")
async def get_version() -> dict[str, str]:
    """Get API version information.

    Returns:
        Version information including API version and environment.
    """
    return {
        "version": __version__,
        "api_version": settings.api_version,
        "environment": settings.environment,
    }
