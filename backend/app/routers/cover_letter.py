from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.models.resume import Resume
from app.schemas.cover_letter import (
    CoverLetterCreate,
    CoverLetterUpdate,
    CoverLetterResponse,
    CoverLetterDuplicateRequest,
    CoverLetterRenameRequest,
    CoverLetterGenerateRequest,
    CoverLetterAIEditsRequest,
    VersionRestoreRequest,
)
from app.schemas.cover_letter_ai import GenerateCoverLetterRequest, GenerateCoverLetterResponse, AICoverLetterEditRequest, AICoverLetterEditResponse
from app.services.cover_letter_service import CoverLetterService
from app.providers.gemini import GeminiProvider

router = APIRouter(prefix="/api/cover-letter", tags=["CoverLetter"])


def _get_ai_provider():
    """Get AI provider instance."""
    return GeminiProvider()


def _build_generation_prompt(
    resume_data: dict,
    job_title: str,
    company_name: str,
    job_description: Optional[str],
    tone: str,
) -> str:
    """Build prompt for cover letter generation."""
    resume_text = ""
    if resume_data:
        if resume_data.get("personal_info"):
            pi = resume_data["personal_info"]
            resume_text += f"Name: {pi.get('name', '')}\n"
            resume_text += f"Email: {pi.get('email', '')}\n"
            resume_text += f"Phone: {pi.get('phone', '')}\n"
            resume_text += f"Location: {pi.get('location', '')}\n\n"

        if resume_data.get("summary"):
            resume_text += f"Summary: {resume_data['summary']}\n\n"

        if resume_data.get("experience"):
            resume_text += "Experience:\n"
            for exp in resume_data["experience"]:
                resume_text += f"- {exp.get('title', '')} at {exp.get('company', '')} ({exp.get('start_date', '')} - {exp.get('end_date', '')}): {exp.get('description', '')}\n"
            resume_text += "\n"

        if resume_data.get("skills"):
            resume_text += f"Skills: {', '.join(resume_data['skills'])}\n\n"

        if resume_data.get("education"):
            resume_text += "Education:\n"
            for edu in resume_data["education"]:
                resume_text += f"- {edu.get('degree', '')} at {edu.get('institution', '')} ({edu.get('year', '')})\n"

    prompt = f"""Write a {tone} cover letter for a job application.

Job Title: {job_title}
Company: {company_name}
"""
    if job_description:
        prompt += f"Job Description: {job_description}\n"

    if resume_text:
        prompt += f"\nCandidate Resume:\n{resume_text}\n"

    prompt += """
Write a compelling cover letter that:
1. Addresses the hiring manager professionally
2. Highlights relevant skills and experience
3. Explains why the candidate is a great fit for this role
4. Has a strong closing statement

Keep it concise (250-400 words) and ATS-friendly. Use standard business letter format.
"""

    return prompt


def _build_edit_prompt(action: str, content: str, job_title: Optional[str], company_name: Optional[str]) -> str:
    """Build prompt for AI editing actions."""
    if action == "improve":
        return f"""Improve this cover letter to make it more compelling and professional:

{content}

{f"For {job_title} at {company_name}" if job_title and company_name else ""}

Make it more impactful while keeping the same length."""
    elif action == "rewrite":
        return f"""Rewrite this cover letter with a fresh perspective:

{content}

{f"For {job_title} at {company_name}" if job_title and company_name else ""}

Keep it professional and engaging."""
    elif action == "shorten":
        return f"""Shorten this cover letter while keeping the key points:

{content}

Reduce to ~150-200 words. Keep the essential message."""
    elif action == "expand":
        return f"""Expand this cover letter with more detail:

{content}

Add more specific examples and details (350-450 words)."""
    elif action == "grammar_fix":
        return f"""Fix any grammar, spelling, and punctuation errors in this cover letter:

{content}

Return the corrected version."""
    elif action == "ats_optimize":
        return f"""Optimize this cover letter for ATS systems (Applicant Tracking Systems):

{content}

- Include relevant keywords from the job description
- Use standard formatting
- Avoid tables, images, or special characters
- Keep it simple and text-based"""
    else:
        return f"""{content}"""


@router.post("", response_model=CoverLetterResponse, status_code=status.HTTP_201_CREATED)
def create_cover_letter(
    cover_letter_data: CoverLetterCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new cover letter."""
    cover_letter = CoverLetterService.create(db, current_user.id, cover_letter_data)
    return cover_letter


@router.get("/archived/list", response_model=List[CoverLetterResponse])
def list_archived_cover_letters(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all archived cover letters for the current user."""
    cover_letters = CoverLetterService.get_archived(db, current_user.id, skip, limit)
    return cover_letters


@router.get("/search", response_model=List[CoverLetterResponse])
def search_cover_letters(
    q: Optional[str] = Query(None, min_length=1),
    sort: str = Query("updated_at", pattern="^(updated_at|created_at|title)$"),
    include_archived: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Search cover letters by query string."""
    if q:
        cover_letters = CoverLetterService.search(db, current_user.id, q, include_archived)
    else:
        cover_letters = CoverLetterService.get_all_sorted(db, current_user.id, sort, include_archived)
    return cover_letters


@router.get("/{cover_letter_id}", response_model=CoverLetterResponse)
def get_cover_letter(
    cover_letter_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a cover letter by ID."""
    cover_letter = CoverLetterService.get_by_id(db, cover_letter_id, current_user.id)
    return cover_letter


@router.get("", response_model=List[CoverLetterResponse])
def list_cover_letters(
    resume_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all cover letters for the current user."""
    cover_letters = CoverLetterService.get_all(db, current_user.id, resume_id, skip, limit)
    return cover_letters


@router.put("/{cover_letter_id}", response_model=CoverLetterResponse)
def update_cover_letter(
    cover_letter_id: int,
    cover_letter_data: CoverLetterUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a cover letter."""
    cover_letter = CoverLetterService.update(db, cover_letter_id, current_user.id, cover_letter_data)
    return cover_letter


@router.delete("/{cover_letter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cover_letter(
    cover_letter_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a cover letter."""
    CoverLetterService.delete(db, cover_letter_id, current_user.id)
    return None


@router.post("/{cover_letter_id}/duplicate", response_model=CoverLetterResponse)
def duplicate_cover_letter(
    cover_letter_id: int,
    duplicate_data: CoverLetterDuplicateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Duplicate a cover letter."""
    new_cover_letter = CoverLetterService.duplicate(
        db,
        cover_letter_id,
        current_user.id,
        duplicate_data.title,
    )
    return new_cover_letter


@router.post("/{cover_letter_id}/rename", response_model=CoverLetterResponse)
def rename_cover_letter(
    cover_letter_id: int,
    rename_data: CoverLetterRenameRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Rename a cover letter."""
    cover_letter = CoverLetterService.rename(db, cover_letter_id, current_user.id, rename_data.title)
    return cover_letter


@router.get("/{cover_letter_id}/versions", response_model=List[dict])
def get_version_history(
    cover_letter_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get version history for a cover letter."""
    versions = CoverLetterService.get_version_history(db, cover_letter_id, current_user.id)
    return versions


@router.post("/{cover_letter_id}/archive", response_model=CoverLetterResponse)
def archive_cover_letter(
    cover_letter_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Archive a cover letter."""
    cover_letter = CoverLetterService.archive(db, cover_letter_id, current_user.id)
    return cover_letter


@router.post("/{cover_letter_id}/restore", response_model=CoverLetterResponse)
def restore_cover_letter(
    cover_letter_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Restore an archived cover letter."""
    cover_letter = CoverLetterService.restore(db, cover_letter_id, current_user.id)
    return cover_letter


@router.post("/{cover_letter_id}/versions/{version}/restore", response_model=CoverLetterResponse)
def restore_version(
    cover_letter_id: int,
    version_data: VersionRestoreRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Restore a specific version of the cover letter."""
    cover_letter = CoverLetterService.restore_version(db, cover_letter_id, current_user.id, version_data.version)
    return cover_letter


# AI Generation endpoints
@router.post("/generate", response_model=GenerateCoverLetterResponse)
def generate_ai_cover_letter(
    request: GenerateCoverLetterRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate a cover letter using AI."""
    provider = _get_ai_provider()

    # Get resume data if provided
    resume_data = None
    if request.resume_id:
        resume = db.query(Resume).filter(
            Resume.id == request.resume_id,
            Resume.user_id == current_user.id,
        ).first()
        if resume:
            resume_data = resume.content

    prompt = _build_generation_prompt(
        resume_data,
        request.job_title,
        request.company_name,
        request.job_description,
        request.tone,
    )

    content = provider._generate_content(prompt)

    return GenerateCoverLetterResponse(content=content)


@router.post("/{cover_letter_id}/generate", response_model=CoverLetterGenerateRequest)
def generate_for_existing(
    cover_letter_id: int,
    request: GenerateCoverLetterRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate and save a cover letter for an existing cover letter."""
    cover_letter = CoverLetterService.get_by_id(db, cover_letter_id, current_user.id)
    provider = _get_ai_provider()

    # Get resume data if provided
    resume_data = None
    if request.resume_id:
        resume = db.query(Resume).filter(
            Resume.id == request.resume_id,
            Resume.user_id == current_user.id,
        ).first()
        if resume:
            resume_data = resume.content

    prompt = _build_generation_prompt(
        resume_data,
        request.job_title,
        request.company_name,
        request.job_description,
        request.tone,
    )

    content = provider._generate_content(prompt)

    # Update the cover letter
    from app.schemas.cover_letter import CoverLetterUpdate
    update_data = CoverLetterUpdate(
        content=content,
        job_title=request.job_title,
        company_name=request.company_name,
        job_description=request.job_description,
        tone=request.tone,
    )

    cover_letter = CoverLetterService.update(db, cover_letter_id, current_user.id, update_data)
    return cover_letter


# AI Editing endpoints
@router.post("/{cover_letter_id}/edit", response_model=AICoverLetterEditResponse)
def ai_edit_cover_letter(
    cover_letter_id: int,
    request: AICoverLetterEditRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Apply AI editing action to a cover letter."""
    cover_letter = CoverLetterService.get_by_id(db, cover_letter_id, current_user.id)
    provider = _get_ai_provider()

    content = request.content or cover_letter.content or ""
    job_title = request.job_title or cover_letter.job_title
    company_name = request.company_name or cover_letter.company_name

    # Validate action
    valid_actions = ["improve", "rewrite", "shorten", "expand", "grammar_fix", "ats_optimize"]
    if request.action not in valid_actions:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {', '.join(valid_actions)}")

    prompt = _build_edit_prompt(request.action, content, job_title, company_name)
    new_content = provider._generate_content(prompt)

    return AICoverLetterEditResponse(content=new_content)


@router.post("/{cover_letter_id}/apply-edit", response_model=CoverLetterResponse)
def apply_ai_edit(
    cover_letter_id: int,
    request: AICoverLetterEditRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Apply and save AI edit to a cover letter."""
    cover_letter = CoverLetterService.get_by_id(db, cover_letter_id, current_user.id)
    provider = _get_ai_provider()

    content = request.content or cover_letter.content or ""
    job_title = request.job_title or cover_letter.job_title
    company_name = request.company_name or cover_letter.company_name

    # Validate action
    valid_actions = ["improve", "rewrite", "shorten", "expand", "grammar_fix", "ats_optimize"]
    if request.action not in valid_actions:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {', '.join(valid_actions)}")

    prompt = _build_edit_prompt(request.action, content, job_title, company_name)
    new_content = provider._generate_content(prompt)

    # Update the cover letter
    from app.schemas.cover_letter import CoverLetterUpdate
    update_data = CoverLetterUpdate(content=new_content)

    cover_letter = CoverLetterService.update(db, cover_letter_id, current_user.id, update_data)
    return cover_letter