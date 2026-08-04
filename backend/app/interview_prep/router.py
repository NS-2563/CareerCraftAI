import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_active_user
from app.core.limiter import limiter
from app.models.user import User
from app.interview_prep.schemas import (
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    EvaluateAnswerRequest,
    EvaluateAnswerResponse,
    CreateSessionRequest,
    UpdateSessionRequest,
    CreateRealInterviewRequest,
    SessionDetail,
    ProgressResponse,
)
from app.interview_prep.service import InterviewPrepService
from app.utils.response import success_response, paginated_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/interview-prep", tags=["Interview Prep"])


@router.post("/generate-questions", response_model=GenerateQuestionsResponse, status_code=status.HTTP_200_OK)
@limiter.limit(f"{settings.RATE_LIMIT_INTERVIEW_PREP};{settings.RATE_LIMIT_INTERVIEW_PREP_DAILY}")
def generate_questions(
    request: Request,
    body: GenerateQuestionsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    questions = InterviewPrepService.generate_questions(
        db=db,
        user_id=current_user.id,
        request=body,
    )
    return GenerateQuestionsResponse(questions=questions)


@router.post("/sessions", response_model=SessionDetail, status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.RATE_LIMIT_INTERVIEW_PREP};{settings.RATE_LIMIT_INTERVIEW_PREP_DAILY}")
def create_session(
    request: Request,
    body: CreateSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    session = InterviewPrepService.create_session(
        db=db,
        user_id=current_user.id,
        request=body,
    )
    return session


@router.put("/sessions/{session_id}", response_model=SessionDetail)
@limiter.limit(f"{settings.RATE_LIMIT_INTERVIEW_PREP};{settings.RATE_LIMIT_INTERVIEW_PREP_DAILY}")
def update_session(
    request: Request,
    session_id: int,
    body: UpdateSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    session = InterviewPrepService.update_session(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
        request=body,
    )
    return session


@router.post("/real-interviews", response_model=SessionDetail, status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.RATE_LIMIT_INTERVIEW_PREP};{settings.RATE_LIMIT_INTERVIEW_PREP_DAILY}")
def create_real_interview(
    request: Request,
    body: CreateRealInterviewRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Log how a real interview for an application went (retrospective)."""
    session = InterviewPrepService.create_real_interview(
        db=db,
        user_id=current_user.id,
        request=body,
    )
    return session


@router.get("/applications/{job_application_id}/real-interviews", response_model=List[SessionDetail])
def list_real_interviews_for_application(
    request: Request,
    job_application_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return real-interview logs tied to one of the user's applications."""
    sessions = InterviewPrepService.list_real_interviews_for_application(
        db=db,
        user_id=current_user.id,
        job_application_id=job_application_id,
    )
    return sessions


@router.get("/applications/{job_application_id}/sessions", response_model=List[SessionDetail])
def list_sessions_for_application(
    request: Request,
    job_application_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return ALL interview sessions (practice + real-interview logs) tied to a
    job application, oldest first, for the per-application timeline.
    """
    sessions = InterviewPrepService.list_sessions_for_application(
        db=db,
        user_id=current_user.id,
        job_application_id=job_application_id,
    )
    return sessions


@router.get("/sessions", response_model=dict)
def list_sessions(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    session_type: Optional[str] = Query(default=None, pattern=r"^(practice|real_interview)$"),
):
    items, pagination = InterviewPrepService.list_sessions(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        session_type=session_type,
    )
    return paginated_response(items, pagination["total"], page, page_size)


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(
    request: Request,
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    session = InterviewPrepService.get_session(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
    )
    return session


@router.get("/progress", response_model=ProgressResponse)
def get_progress(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    sort: str = Query(default="score_asc", pattern=r"^(score_asc|score_desc|recent|session_count)$"),
):
    result = InterviewPrepService.get_progress(
        db=db,
        user_id=current_user.id,
        sort=sort,
    )
    return result


@router.post("/evaluate-answer", response_model=EvaluateAnswerResponse, status_code=status.HTTP_200_OK)
@limiter.limit(f"{settings.RATE_LIMIT_INTERVIEW_EVAL};{settings.RATE_LIMIT_INTERVIEW_EVAL_DAILY}")
def evaluate_answer(
    request: Request,
    body: EvaluateAnswerRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    result = InterviewPrepService.evaluate_answer(request=body)
    return result
