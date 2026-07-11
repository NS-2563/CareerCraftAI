from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.resume import (
    ResumeCreate,
    ResumeUpdate,
    ResumeResponse,
    ResumeDuplicateRequest,
    ResumeRenameRequest,
    VersionRestoreRequest,
)
from app.services.resume_service import ResumeService
from app.utils.response import success_response, paginated_response
from app.utils.exceptions import NotFoundException
from app.utils.resume_serializer import serialize_resume

router = APIRouter(prefix="/api/resume", tags=["Resume"])


# Non-specific routes first (must come before /{resume_id})
@router.get("/search", response_model=List[ResumeResponse])
def search_resumes(
    q: Optional[str] = Query(None, min_length=1),
    sort: str = Query("updated_at", regex="^(updated_at|created_at|name)$"),
    include_archived: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Search resumes by query string."""
    if q:
        resumes = ResumeService.search(db, current_user.id, q, include_archived)
    else:
        resumes = ResumeService.get_all_sorted(db, current_user.id, sort, include_archived)
    return resumes


@router.get("/archived/list", response_model=List[ResumeResponse])
def list_archived_resumes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all archived resumes for the current user."""
    resumes = ResumeService.get_archived(db, current_user.id, skip, limit)
    return resumes


@router.get("", response_model=List[ResumeResponse])
def list_resumes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all resumes for the current user."""
    resumes = ResumeService.get_all(db, current_user.id, skip, limit)
    return resumes


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
def create_resume(
    resume_data: ResumeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new resume."""
    resume = ResumeService.create(db, current_user.id, resume_data)
    return serialize_resume(resume)


# Routes with resume_id parameter (must come after non-specific routes)
@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a resume by ID."""
    resume = ResumeService.get_by_id(db, resume_id, current_user.id)
    return serialize_resume(resume)


@router.put("/{resume_id}", response_model=ResumeResponse)
def update_resume(
    resume_id: int,
    resume_data: ResumeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a resume."""
    resume = ResumeService.update(db, resume_id, current_user.id, resume_data)
    return serialize_resume(resume)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a resume."""
    ResumeService.delete(db, resume_id, current_user.id)
    return None


@router.post("/{resume_id}/duplicate", response_model=ResumeResponse)
def duplicate_resume(
    resume_id: int,
    duplicate_data: ResumeDuplicateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Duplicate a resume."""
    new_resume = ResumeService.duplicate(
        db,
        resume_id,
        current_user.id,
        duplicate_data.name,
    )
    return serialize_resume(new_resume)


@router.post("/{resume_id}/rename", response_model=ResumeResponse)
def rename_resume(
    resume_id: int,
    rename_data: ResumeRenameRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Rename a resume."""
    resume = ResumeService.rename(db, resume_id, current_user.id, rename_data.name)
    return serialize_resume(resume)


@router.get("/{resume_id}/versions", response_model=List[dict])
def get_version_history(
    resume_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get version history for a resume."""
    versions = ResumeService.get_version_history(db, resume_id, current_user.id)
    return versions


@router.post("/{resume_id}/archive", response_model=ResumeResponse)
def archive_resume(
    resume_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Archive a resume."""
    resume = ResumeService.archive(db, resume_id, current_user.id)
    return serialize_resume(resume)


@router.post("/{resume_id}/restore", response_model=ResumeResponse)
def restore_resume(
    resume_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Restore an archived resume."""
    resume = ResumeService.restore(db, resume_id, current_user.id)
    return serialize_resume(resume)


@router.post("/{resume_id}/restore-version", response_model=ResumeResponse)
def restore_version(
    resume_id: int,
    version_data: VersionRestoreRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Restore a specific version of the resume."""
    resume = ResumeService.restore_version(db, resume_id, current_user.id, version_data.version)
    return serialize_resume(resume)