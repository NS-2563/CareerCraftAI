from fastapi import APIRouter, Depends, status, Query, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import logging

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
from app.utils.exceptions import ValidationException
from app.utils.resume_serializer import serialize_resume
from app.utils.upload import save_upload, MAX_UPLOAD_SIZE
from app.resume.services.pdf_parser import extract_text_from_pdf
from app.resume.services.resume_pipeline import parse_resume_full
from app.analytics.service import AnalyticsService

logger = logging.getLogger(__name__)

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
    archived: bool | None = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    resumes = ResumeService.get_all(
        db,
        current_user.id,
        skip,
        limit,
        archived,
    )
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


@router.post("/import", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def import_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Import a PDF resume. Parses the text and creates a resume record."""
    content = await file.read()

    try:
        file_path = save_upload(content, file.filename or "resume.pdf")
    except ValueError as e:
        raise ValidationException(str(e))

    try:
        extracted_text = extract_text_from_pdf(file_path)
    except Exception as e:
        logger.error("PDF parsing failed for file %s: %s", file.filename, str(e))
        raise ValidationException("Could not parse the PDF file. Ensure it is a valid PDF.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    filename_stem = os.path.splitext(file.filename or "resume.pdf")[0]
    resume_name = f"Imported - {filename_stem}"

    # Phase 2B→2C→2D pipeline: section detection → deterministic → AI enrichment
    pipeline_result = parse_resume_full(
        raw_text=extracted_text or "",
        resume_name=resume_name,
        use_ai=True,
    )

    resume_data = pipeline_result["resume_create"]
    resume = ResumeService.create(db, current_user.id, resume_data)

    ai_used = pipeline_result.get("ai_used", False)
    source_meta = pipeline_result.get("source_meta", {})
    sections_ai_success = sum(
        1 for v in source_meta.values() if isinstance(v, dict) and v.get("ai_success")
    )
    sections_total = len(source_meta)

    logger.info(
        "IMPORT resume_id=%s user_id=%s filename=%s ai=%s sections=%d/%d",
        resume.id, current_user.id, file.filename,
        ai_used, sections_ai_success, sections_total,
    )

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


@router.get("/{resume_id}/score-history")
def get_resume_score_history(
    resume_id: int,
    metric_type: str = Query("ats_score", regex="^(ats_score|resume_score)$"),
    limit: int = Query(20, ge=2, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return the ATS/resume score history for a saved resume (oldest first).

    Includes the latest and previous snapshot values plus the delta so the UI
    can render a before/after trend. 404s for a resume the user does not own.
    """
    resume = ResumeService.get_by_id(db, resume_id, current_user.id)

    snapshots = AnalyticsService.get_history(
        db,
        current_user.id,
        metric_type,
        resume_id=resume_id,
        limit=limit,
    )

    items = [
        {
            "id": snapshot.id,
            "value": snapshot.value,
            "recorded_at": snapshot.recorded_at,
        }
        for snapshot in snapshots
    ]

    latest = items[-1]["value"] if items else None
    previous = items[-2]["value"] if len(items) >= 2 else None
    change = round(latest - previous, 1) if (latest is not None and previous is not None) else None

    return {
        "resume_id": resume_id,
        "metric_type": metric_type,
        "snapshots": items,
        "count": len(items),
        "latest": latest,
        "previous": previous,
        "change": change,
    }


@router.get("/{resume_id}/score-history/diff")
def get_resume_score_history_diff(
    resume_id: int,
    from_snapshot_id: int = Query(..., alias="from", description="Source snapshot id"),
    to_snapshot_id: int = Query(..., alias="to", description="Target snapshot id"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return a deterministic diff between two score snapshots of a resume.

    Compares the captured resume content (skills list + summary text) at the
    two snapshot points and reports exactly the computed changes: skills added,
    skills removed, whether the summary text changed, the summary word-count
    delta, and which added skills now cover previously-missing keywords from the
    user's stored JD matches for this resume. No inference — every field traces
    to stored content. 404s for a resume the user does not own.
    """
    from app.analytics.service import compute_content_diff, jd_keywords_now_covered

    ResumeService.get_by_id(db, resume_id, current_user.id)

    from_snap = AnalyticsService.get_snapshot(db, current_user.id, from_snapshot_id)
    to_snap = AnalyticsService.get_snapshot(db, current_user.id, to_snapshot_id)

    if from_snap is None or to_snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    if from_snap.id == to_snap.id:
        raise HTTPException(status_code=400, detail="from and to must be different snapshots")
    if from_snap.resume_id != resume_id or to_snap.resume_id != resume_id:
        raise HTTPException(status_code=400, detail="Snapshots must belong to this resume")
    if from_snap.metric_type != to_snap.metric_type:
        raise HTTPException(status_code=400, detail="Snapshots must be of the same metric type")

    if not from_snap.content_json or not to_snap.content_json:
        raise HTTPException(
            status_code=409,
            detail="Content was not captured for one or both snapshots",
        )

    diff = compute_content_diff(from_snap.content_json, to_snap.content_json)
    covered = jd_keywords_now_covered(
        db, current_user.id, resume_id, diff["skills_added"]
    )

    def _snapshot_summary(snap) -> dict:
        return {
            "snapshot_id": snap.id,
            "value": snap.value,
            "recorded_at": snap.recorded_at.isoformat() if snap.recorded_at else None,
        }

    return {
        "resume_id": resume_id,
        "metric_type": from_snap.metric_type,
        "from": _snapshot_summary(from_snap),
        "to": _snapshot_summary(to_snap),
        "score_delta": round(to_snap.value - from_snap.value, 1),
        "content_available": True,
        "skills_added": diff["skills_added"],
        "skills_removed": diff["skills_removed"],
        "summary_changed": diff["summary_changed"],
        "summary_word_delta": diff["summary_word_delta"],
        "jd_keywords_now_covered": covered,
    }


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