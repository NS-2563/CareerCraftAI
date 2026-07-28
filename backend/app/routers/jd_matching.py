"""JD Matching Router — endpoints for resume-to-job-description matching.

All endpoints require authentication.
JD text is never logged in raw form.
"""
import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.job_tracker import (
    JobDescriptionMatchRequest,
    JobDescriptionMatchResponse,
)
from app.main import limiter
from app.services.jd_match_service import match_resume_to_jd, load_resume_data
from app.utils.exceptions import ValidationException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jd-match", tags=["JD Matching"])


def _sanitize_for_log(jd_text: str) -> str:
    """Return a safe log representation of JD text."""
    length = len(jd_text)
    prefix = jd_text[:80].replace("\n", " ").strip()
    return f"[len={length}] \"{prefix}...\""


@router.post("/analyze", response_model=JobDescriptionMatchResponse)
@limiter.limit(f"{settings.RATE_LIMIT_JD_MATCH};{settings.RATE_LIMIT_JD_MATCH_DAILY}")
def analyze_jd_match(
    request: Request,
    match_req: JobDescriptionMatchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Match a resume against a job description.

    Accepts either inline resume_data or a saved resume_id.
    Deterministic matching always runs; AI semantic matching is opt-in.

    Protection:
    - JD text is limited to 10000 characters
    - Auth required
    - JD text is not logged in raw form
    - Resume ownership verified when using resume_id
    """
    if not match_req.jd_text or not match_req.jd_text.strip():
        raise ValidationException("Job description text is required")

    log_safe = _sanitize_for_log(match_req.jd_text)
    logger.info(
        "JD match requested by user %s: %s, ai=%s",
        current_user.id, log_safe, match_req.enable_ai,
    )

    try:
        resume_data = load_resume_data(
            db=db,
            resume_id=match_req.resume_id,
            user_id=current_user.id,
            resume_data=match_req.resume_data,
        )
    except Exception as e:
        raise ValidationException(f"Failed to load resume data: {str(e)}")

    try:
        result = match_resume_to_jd(
            resume_data=resume_data,
            jd_text=match_req.jd_text,
            enable_ai=match_req.enable_ai,
        )
    except ValueError as e:
        raise ValidationException(str(e))

    return JobDescriptionMatchResponse(**result)


@router.post(
    "/analyze-saved/{job_id}",
    response_model=JobDescriptionMatchResponse,
)
@limiter.limit(f"{settings.RATE_LIMIT_JD_MATCH};{settings.RATE_LIMIT_JD_MATCH_DAILY}")
def analyze_saved_jd(
    request: Request,
    job_id: int,
    enable_ai: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Match a resume against a saved job description from the Job Tracker.

    Loads the job_description and resume_id from the saved job application.
    """
    from app.models.job_application import JobApplication
    from app.utils.exceptions import NotFoundException

    job = db.query(JobApplication).filter(
        JobApplication.id == job_id,
        JobApplication.user_id == current_user.id,
    ).first()

    if not job:
        raise NotFoundException("JobApplication", str(job_id))

    if not job.job_description or not job.job_description.strip():
        raise ValidationException("This job application has no saved job description")

    if not job.resume_id:
        raise ValidationException("This job application has no linked resume")

    log_safe = _sanitize_for_log(job.job_description)
    logger.info(
        "Saved JD match requested by user %s: job_id=%d, %s, ai=%s",
        current_user.id, job_id, log_safe, enable_ai,
    )

    try:
        resume_data = load_resume_data(
            db=db,
            resume_id=job.resume_id,
            user_id=current_user.id,
            resume_data=None,
        )
    except Exception as e:
        raise ValidationException(f"Failed to load resume data: {str(e)}")

    try:
        result = match_resume_to_jd(
            resume_data=resume_data,
            jd_text=job.job_description,
            enable_ai=enable_ai,
        )
    except ValueError as e:
        raise ValidationException(str(e))

    return JobDescriptionMatchResponse(**result)
