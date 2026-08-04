import logging
from fastapi import APIRouter, Depends, Request, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json

logger = logging.getLogger(__name__)

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_active_user
from app.core.limiter import limiter
from app.models.user import User
from app.models.job_application import JobApplication
from app.models.resume import Resume
from app.communication.schemas import (
    CommunicationMessageCreate,
    CommunicationMessageUpdate,
    CommunicationMessageResponse,
    GenerateMessageRequest,
    LogInboundMessageRequest,
    RenameRequest,
    DuplicateRequest,
    VersionRestoreRequest,
    ConversationStatusUpdateRequest,
    ConversationStatusResponse,
    ApplicationConversationStatus,
)
from app.communication.service import CommunicationService
from app.communication.thread_summary import attach_thread_summary
from app.providers.factory import get_provider
from app.utils.exceptions import NotFoundException

router = APIRouter(prefix="/api/communication", tags=["Communication"])


def _build_resume_summary(resume: Resume) -> str:
    try:
        personal = json.loads(resume.personal) if resume.personal else {}
    except Exception:
        personal = {}
    name = personal.get("name") or personal.get("first_name", "")
    if personal.get("last_name"):
        name = f"{name} {personal['last_name']}".strip()

    try:
        skills = json.loads(resume.skills) if resume.skills else []
    except Exception:
        skills = []
    skill_names = []
    for s in skills:
        if isinstance(s, dict):
            skill_names.append(s.get("name", ""))
        elif isinstance(s, str):
            skill_names.append(s)

    try:
        experience = json.loads(resume.experience) if resume.experience else []
    except Exception:
        experience = []
    most_recent = None
    if experience:
        most_recent = experience[0]
        if isinstance(most_recent, dict):
            most_recent = f"{most_recent.get('position', '')} at {most_recent.get('company', '')}"

    parts = []
    if name:
        parts.append(f"Candidate: {name}")
    if resume.summary:
        parts.append(f"Summary: {resume.summary}")
    if skill_names:
        parts.append(f"Skills: {', '.join(skill_names[:10])}")
    if most_recent:
        parts.append(f"Most Recent Role: {most_recent}")
    return " | ".join(parts) if parts else ""


@router.post("/generate", response_model=CommunicationMessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.RATE_LIMIT_COMMUNICATION};{settings.RATE_LIMIT_COMMUNICATION_DAILY}")
def generate_message(
    request: Request,
    body: GenerateMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    provider = get_provider()
    logger.debug("generate_message: message_type=%s provider=%s model=%s", body.message_type, provider.__class__.__name__, getattr(provider, 'model_name', 'UNKNOWN'))

    auto_recipient_company = body.recipient_company
    auto_recipient_role = body.recipient_role
    custom_context = body.custom_context or ""
    resume_summary = None

    if body.related_job_application_id is not None:
        job = db.query(JobApplication).filter(
            JobApplication.id == body.related_job_application_id,
            JobApplication.user_id == current_user.id,
        ).first()
        if job:
            if not auto_recipient_company:
                auto_recipient_company = job.company
            if not auto_recipient_role:
                auto_recipient_role = job.job_title
            if job.job_description:
                context_snippet = f"Job at {job.company}: {job.job_title}.\nDescription: {job.job_description[:500]}"
                if custom_context:
                    custom_context = f"{custom_context}\n\n{context_snippet}"
                else:
                    custom_context = context_snippet

    if body.related_resume_id is not None:
        resume = db.query(Resume).filter(
            Resume.id == body.related_resume_id,
            Resume.user_id == current_user.id,
        ).first()
        if resume:
            resume_summary = _build_resume_summary(resume)

    if body.message_type == "cold_email":
        result = provider.generate_cold_email(
            recipient_name=body.recipient_name,
            recipient_role=auto_recipient_role,
            recipient_company=auto_recipient_company,
            tone=body.tone,
            custom_context=custom_context,
            resume_summary=resume_summary,
        )
    elif body.message_type == "follow_up":
        result = provider.generate_follow_up(
            recipient_name=body.recipient_name,
            recipient_company=auto_recipient_company,
            tone=body.tone,
            custom_context=custom_context,
        )
    elif body.message_type == "thank_you":
        result = provider.generate_thank_you(
            recipient_name=body.recipient_name,
            recipient_company=auto_recipient_company,
            tone=body.tone,
            custom_context=custom_context,
        )
    elif body.message_type == "linkedin_note":
        result = provider.generate_linkedin_note(
            recipient_name=body.recipient_name,
            recipient_role=auto_recipient_role,
            recipient_company=auto_recipient_company,
            tone=body.tone,
            custom_context=custom_context,
            resume_summary=resume_summary,
        )
    elif body.message_type == "referral_request":
        result = provider.generate_referral_request(
            recipient_name=body.recipient_name,
            recipient_role=auto_recipient_role,
            recipient_company=auto_recipient_company,
            tone=body.tone,
            custom_context=custom_context,
            resume_summary=resume_summary,
        )
    elif body.message_type == "recruiter_reply":
        thread_context = None
        if body.thread_context and body.related_job_application_id is not None:
            job = db.query(JobApplication).filter(
                JobApplication.id == body.related_job_application_id,
                JobApplication.user_id == current_user.id,
            ).first()
            if job:
                recent = CommunicationService.get_recent_thread(
                    db, current_user.id, body.related_job_application_id, n=5
                )
                thread_context = [
                    {
                        "direction": m.direction,
                        "sender_name": m.sender_name or m.recipient_name,
                        "recipient_name": m.recipient_name,
                        "subject": m.subject,
                        "body": m.body,
                        "created_at": m.created_at,
                    }
                    for m in recent
                ]
        result = provider.generate_recruiter_reply(
            inbound_message=body.inbound_message,
            reply_intent=body.reply_intent,
            recipient_name=body.recipient_name,
            recipient_company=auto_recipient_company,
            tone=body.tone,
            custom_context=custom_context,
            thread_context=thread_context,
        )
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unknown message_type: {body.message_type}")

    subject = result.get("subject", "") if body.message_type != "linkedin_note" else ""
    message_body = result.get("body", "")

    message = CommunicationService.create_from_generation(
        db=db,
        user_id=current_user.id,
        message_type=body.message_type,
        tone=body.tone,
        recipient_name=body.recipient_name,
        recipient_role=auto_recipient_role,
        recipient_company=auto_recipient_company,
        subject=subject,
        body=message_body,
        related_job_application_id=body.related_job_application_id,
        related_resume_id=body.related_resume_id,
    )
    return message


@router.post("/log-inbound", response_model=CommunicationMessageResponse, status_code=status.HTTP_201_CREATED)
def log_inbound_email(
    body: LogInboundMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Log a manually pasted inbound recruiter email against a job application.

    Ownership-checked: the job application must belong to the current user.
    """
    job = db.query(JobApplication).filter(
        JobApplication.id == body.related_job_application_id,
        JobApplication.user_id == current_user.id,
    ).first()
    if not job:
        raise NotFoundException("JobApplication", str(body.related_job_application_id))

    message = CommunicationService.log_inbound(
        db=db,
        user_id=current_user.id,
        related_job_application_id=body.related_job_application_id,
        body=body.body,
        sender_name=body.sender_name,
        sender_email=body.sender_email,
        subject=body.subject,
        received_at=body.received_at,
    )
    return message


@router.get("/thread/{job_application_id}", response_model=List[CommunicationMessageResponse])
def get_thread(
    job_application_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return the full conversation thread (both directions) for an application.

    Ownership-checked: the job application must belong to the current user.
    """
    job = db.query(JobApplication).filter(
        JobApplication.id == job_application_id,
        JobApplication.user_id == current_user.id,
    ).first()
    if not job:
        raise NotFoundException("JobApplication", str(job_application_id))

    messages = CommunicationService.get_thread(db, current_user.id, job_application_id)
    messages = CommunicationService.attach_conversation_status(db, messages)
    return attach_thread_summary(db, messages)


@router.get("/conversation-status/{job_application_id}", response_model=ConversationStatusResponse)
def get_conversation_status(
    job_application_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Resolved conversation status for one application (Needs Reply/Waiting/Closed).

    Ownership-checked; 404 for another user's application.
    """
    return CommunicationService.get_conversation_status(db, current_user.id, job_application_id)


@router.put("/conversation-status/{job_application_id}", response_model=ConversationStatusResponse)
def set_conversation_status(
    job_application_id: int,
    body: ConversationStatusUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Set or clear the manual conversation-status override for an application."""
    return CommunicationService.set_conversation_status(
        db, current_user.id, job_application_id, body.status
    )


@router.get("/conversation-statuses", response_model=List[ApplicationConversationStatus])
def list_conversation_statuses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Cross-application conversation statuses (Communication Hub needs-attention view)."""
    return CommunicationService.get_all_conversation_statuses(db, current_user.id)


@router.post("", response_model=CommunicationMessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    message_data: CommunicationMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    message = CommunicationService.create(db, current_user.id, message_data)
    return message


@router.get("", response_model=List[CommunicationMessageResponse])
def list_messages(
    message_type: Optional[str] = Query(None, pattern=r"^(cold_email|follow_up|thank_you|linkedin_note|referral_request|recruiter_reply|recruiter_email)$"),
    archived: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    messages = CommunicationService.get_all(db, current_user.id, message_type, archived, skip, limit)
    messages = CommunicationService.attach_conversation_status(db, messages)
    return attach_thread_summary(db, messages)


@router.get("/{message_id}", response_model=CommunicationMessageResponse)
def get_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    message = CommunicationService.get_by_id(db, message_id, current_user.id)
    return message


@router.put("/{message_id}", response_model=CommunicationMessageResponse)
def update_message(
    message_id: int,
    message_data: CommunicationMessageUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    message = CommunicationService.update(db, message_id, current_user.id, message_data)
    return message


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    CommunicationService.delete(db, message_id, current_user.id)
    return None


@router.post("/{message_id}/duplicate", response_model=CommunicationMessageResponse)
def duplicate_message(
    message_id: int,
    duplicate_data: DuplicateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    new_message = CommunicationService.duplicate(db, message_id, current_user.id, duplicate_data.title)
    return new_message


@router.post("/{message_id}/rename", response_model=CommunicationMessageResponse)
def rename_message(
    message_id: int,
    rename_data: RenameRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    message = CommunicationService.rename(db, message_id, current_user.id, rename_data.title)
    return message


@router.post("/{message_id}/archive", response_model=CommunicationMessageResponse)
def archive_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    message = CommunicationService.archive(db, message_id, current_user.id)
    return message


@router.post("/{message_id}/restore", response_model=CommunicationMessageResponse)
def restore_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    message = CommunicationService.restore(db, message_id, current_user.id)
    return message


@router.get("/{message_id}/versions", response_model=List[dict])
def get_version_history(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    versions = CommunicationService.get_version_history(db, message_id, current_user.id)
    return versions


@router.post("/{message_id}/restore-version", response_model=CommunicationMessageResponse)
def restore_version(
    message_id: int,
    version_data: VersionRestoreRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    message = CommunicationService.restore_version(db, message_id, current_user.id, version_data.version)
    return message
