from fastapi import APIRouter, Depends

from app.dependencies import get_current_active_user
from app.models.user import User
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
def generate_summary(
    request: GenerateSummaryRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Generate a professional summary from personal info."""
    personal = request.model_dump()
    summary = AIService.generate_summary(personal)
    return GenerateSummaryResponse(summary=sanitize_ai_output(summary))


@router.post("/improve-summary", response_model=ImproveSummaryResponse)
def improve_summary(
    request: ImproveSummaryRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Improve an existing summary."""
    improved = AIService.improve_summary(request.text)
    return ImproveSummaryResponse(improved_text=sanitize_ai_output(improved))


@router.post("/improve-experience", response_model=ImproveExperienceResponse)
def improve_experience(
    request: ImproveExperienceRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Improve experience description."""
    improved = AIService.improve_experience(
        request.text,
        request.position,
        request.company,
    )
    return ImproveExperienceResponse(improved_text=sanitize_ai_output(improved))


@router.post("/improve-project", response_model=ImproveProjectResponse)
def improve_project(
    request: ImproveProjectRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Improve project description."""
    improved = AIService.improve_project(request.text, request.name)
    return ImproveProjectResponse(improved_text=sanitize_ai_output(improved))


@router.post("/suggest-skills", response_model=SuggestSkillsResponse)
def suggest_skills(
    request: SuggestSkillsRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Suggest relevant skills."""
    result = AIService.suggest_skills(
        request.current_skills,
        request.job_title,
        request.job_description,
    )
    return SuggestSkillsResponse(
        skills=sanitize_ai_output_list(result["skills"]),
        categories=result.get("categories"),
    )


@router.post("/analyze-resume", response_model=AnalyzeResumeResponse)
def analyze_resume(
    request: AnalyzeResumeRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Analyze a resume and provide feedback."""
    result = AIService.analyze_resume(request.resume)
    result["suggestions"] = sanitize_ai_output_list(result.get("suggestions", []))
    result["strengths"] = sanitize_ai_output_list(result.get("strengths", []))
    result["weaknesses"] = sanitize_ai_output_list(result.get("weaknesses", []))
    return AnalyzeResumeResponse(**result)