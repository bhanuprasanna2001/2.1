"""User profile management endpoints."""

from fastapi import APIRouter, status

from app.api.deps import CurrentUserID, UserServiceDep
from app.schemas.user import UserRead, UserUpdate, UserUpdatePassword

router = APIRouter()


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get my profile",
    description="Get the current user's profile information.",
)
async def get_my_profile(
    user_id: CurrentUserID,
    service: UserServiceDep,
) -> UserRead:
    """Get current user's profile.

    Returns the complete user profile including statistics.
    """
    return await service.get_by_id(user_id)


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update my profile",
    description="Update the current user's profile information.",
)
async def update_my_profile(
    data: UserUpdate,
    user_id: CurrentUserID,
    service: UserServiceDep,
) -> UserRead:
    """Update current user's profile.

    Only provided fields will be updated:
    - **display_name**: New display name
    """
    return await service.update(user_id, data)


@router.post(
    "/me/change-password",
    response_model=UserRead,
    summary="Change password",
    description="Change the current user's password.",
)
async def change_password(
    data: UserUpdatePassword,
    user_id: CurrentUserID,
    service: UserServiceDep,
) -> UserRead:
    """Change the current user's password.

    - **current_password**: Current password for verification
    - **new_password**: New password (min 8 chars, must contain letter and number)

    Returns the updated user profile.
    """
    return await service.change_password(user_id, data)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate account",
    description="Deactivate the current user's account (soft delete).",
)
async def deactivate_account(
    password: str,
    user_id: CurrentUserID,
    service: UserServiceDep,
) -> None:
    """Deactivate the current user's account.

    This is a soft delete - the account can potentially be reactivated.
    Requires password confirmation for security.

    **Warning**: This will make your account inaccessible.
    """
    await service.deactivate(user_id, password)
