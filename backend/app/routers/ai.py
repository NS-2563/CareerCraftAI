from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_active_user
from app.core.limiter import limiter
from app.models.user import User
from app.analytics.service import AnalyticsService
from app.schemas.ai import (
    GenerateSummaryRequest,
    GenerateSummaryResponse,
    ImproveSummaryRequest,
    ImproveSummaryResponse,
    ImproveExperienceRequest,
    ImproveExperienceResponse,
    ImproveProjectRequest,
    ImproveProjectResponse,
    SuggestSkillsRequest,
    SuggestSkillsResponse,
    AnalyzeResumeRequest,
    AnalyzeResumeResponse,
)
from app.services.ai_service import AIService
from app.utils.sanitizer import sanitize_ai_output, sanitize_ai_output_list

router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.post("/generate-summary", response_model=GenerateSummaryResponse)
@limiter.limit(f"{settings.RATE_LIMIT_AI};{settings.RATE_LIMIT_AI_DAILY}")
def generate_summary(
    request: Request,
    body: GenerateSummaryRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Generate a professional summary from personal info."""
    personal = body.model_dump()
    summary = AIService.generate_summary(personal)
    return GenerateSummaryResponse(summary=sanitize_ai_output(summary))


@router.post("/improve-summary", response_model=ImproveSummaryResponse)
@limiter.limit(f"{settings.RATE_LIMIT_AI};{settings.RATE_LIMIT_AI_DAILY}")
def improve_summary(
    request: Request,
    body: ImproveSummaryRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Improve an existing summary."""
    improved = AIService.improve_summary(body.text)
    return ImproveSummaryResponse(improved_text=sanitize_ai_output(improved))


@router.post("/improve-experience", response_model=ImproveExperienceResponse)
@limiter.limit(f"{settings.RATE_LIMIT_AI};{settings.RATE_LIMIT_AI_DAILY}")
def improve_experience(
    request: Request,
    body: ImproveExperienceRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Improve experience description."""
    improved = AIService.improve_experience(
        body.text,
        body.position,
        body.company,
    )
    return ImproveExperienceResponse(improved_text=sanitize_ai_output(improved))


@router.post("/improve-project", response_model=ImproveProjectResponse)
@limiter.limit(f"{settings.RATE_LIMIT_AI};{settings.RATE_LIMIT_AI_DAILY}")
def improve_project(
    request: Request,
    body: ImproveProjectRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Improve project description."""
    improved = AIService.improve_project(body.text, body.name)
    return ImproveProjectResponse(improved_text=sanitize_ai_output(improved))


@router.post("/suggest-skills", response_model=SuggestSkillsResponse)
@limiter.limit(f"{settings.RATE_LIMIT_AI};{settings.RATE_LIMIT_AI_DAILY}")
def suggest_skills(
    request: Request,
    body: SuggestSkillsRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Suggest relevant skills."""
    result = AIService.suggest_skills(
        body.current_skills,
        body.job_title,
        body.job_description,
    )
    return SuggestSkillsResponse(
        skills=sanitize_ai_output_list(result["skills"]),
        categories=result.get("categories"),
    )


@router.post("/analyze-resume", response_model=AnalyzeResumeResponse)
@limiter.limit(f"{settings.RATE_LIMIT_AI};{settings.RATE_LIMIT_AI_DAILY}")
def analyze_resume(
    request: Request,
    body: AnalyzeResumeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Analyze a resume and provide feedback."""
    result = AIService.analyze_resume(body.resume)
    if not result.get("analysis_failed"):
        if result.get("ats_score") is not None:
            AnalyticsService.record_snapshot(
                db, current_user.id, "ats_score", float(result["ats_score"]),
            )
        if result.get("resume_score") is not None:
            AnalyticsService.record_snapshot(
                db, current_user.id, "resume_score", float(result["resume_score"]),
            )
    result["suggestions"] = sanitize_ai_output_list(result.get("suggestions", []))
    result["strengths"] = sanitize_ai_output_list(result.get("strengths", []))
    result["weaknesses"] = sanitize_ai_output_list(result.get("weaknesses", []))
    return AnalyzeResumeResponse(**result)