from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from typing import List

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_active_user
from app.core.limiter import limiter
from app.models.user import User
from app.models.job_application import JobApplication
from app.communication.service import CommunicationService
from app.communication.suggestions_service import get_active_suggestions, dismiss_suggestion, mark_actioned
from app.providers.factory import get_provider

router = APIRouter(prefix="/api/communication/suggestions", tags=["Communication Suggestions"])


@router.get("")
def list_suggestions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    suggestions = get_active_suggestions(db, current_user.id)
    return suggestions


@router.post("/{suggestion_id}/dismiss", status_code=status.HTTP_200_OK)
def dismiss_suggestion_endpoint(
    suggestion_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    suggestion = dismiss_suggestion(db, suggestion_id, current_user.id)
    return {
        "id": suggestion.id,
        "is_dismissed": suggestion.is_dismissed,
    }


@router.post("/{suggestion_id}/generate", status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.RATE_LIMIT_COMMUNICATION};{settings.RATE_LIMIT_COMMUNICATION_DAILY}")
def generate_from_suggestion(
    request: Request,
    suggestion_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    suggestion = mark_actioned(db, suggestion_id, current_user.id)

    job = db.query(JobApplication).filter(
        JobApplication.id == suggestion.job_application_id,
        JobApplication.user_id == current_user.id,
    ).first()

    recipient_name = ""
    recipient_company = job.company if job else ""
    recipient_role = job.job_title if job else ""

    provider = get_provider()
    result = provider.generate_follow_up(
        recipient_name=None,
        recipient_company=recipient_company,
        tone="professional",
        custom_context=None,
    )

    subject = result.get("subject", "")
    body = result.get("body", "")

    message = CommunicationService.create_from_generation(
        db=db,
        user_id=current_user.id,
        message_type="follow_up",
        tone="professional",
        recipient_name=recipient_name or None,
        recipient_role=recipient_role,
        recipient_company=recipient_company,
        subject=subject,
        body=body,
        related_job_application_id=suggestion.job_application_id,
    )

    from app.communication.schemas import CommunicationMessageResponse
    return CommunicationMessageResponse.model_validate(message)
