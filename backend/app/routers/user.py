import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.auth_service import AuthService
from app.utils.response import success_response

logger = logging.getLogger("audit.user")

router = APIRouter(prefix="/api/user", tags=["User"])


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_active_user)):
    """Get user profile."""
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update user profile."""
    for field, value in user_data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/data", response_model=dict)
def export_data(current_user: User = Depends(get_current_active_user)):
    """Export all user data."""
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "resumes": [
            {
                "id": r.id,
                "name": r.name,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in current_user.resumes
        ],
        "cover_letters": [
            {
                "id": cl.id,
                "title": cl.title,
                "created_at": cl.created_at.isoformat() if cl.created_at else None,
            }
            for cl in current_user.cover_letters
        ],
        "career_reports": [
            {
                "id": cr.id,
                "created_at": cr.created_at.isoformat() if cr.created_at else None,
            }
            for cr in current_user.career_reports
        ],
        "job_applications": [
            {
                "id": ja.id,
                "company": ja.company,
                "position": ja.position,
                "status": ja.status,
            }
            for ja in current_user.job_applications
        ],
    }


@router.delete("/profile", status_code=status.HTTP_200_OK)
def delete_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete user account and all associated data."""
    db.delete(current_user)
    db.commit()
    logger.info("DELETE_ACCOUNT user_id=%s email=%s", current_user.id, current_user.email)
    return success_response(message="Account deleted successfully")