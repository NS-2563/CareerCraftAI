from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.auth_service import AuthService
from app.utils.response import success_response

router = APIRouter(prefix="/api/user", tags=["User"])


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_active_user)):
    """Get user profile."""
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """Update user profile."""
    # Placeholder - would implement actual profile update
    return current_user


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(current_user: User = Depends(get_current_active_user)):
    """Delete user account."""
    # Placeholder - would implement actual account deletion
    pass