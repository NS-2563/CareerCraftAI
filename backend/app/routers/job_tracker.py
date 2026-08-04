from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.job_tracker.services.job_tracker_service import JobTrackerService
from app.job_tracker.workspace import (
    build_workspace_payload,
    dismiss_insight,
    get_dismissed_keys,
)
from app.schemas.job_tracker import (
    JobApplicationCreate,
    JobApplicationResponse,
    JobApplicationUpdate,
    JobStatsResponse,
)
from app.utils.response import deleted_response, success_response

router = APIRouter(prefix="/api/jobs", tags=["Job Tracker"])


@router.get("", response_model=List[JobApplicationResponse])
def list_jobs(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query(
        "created_at",
        description="Sort field.",
    ),

    descending: bool = Query(True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[JobApplicationResponse]:
    """Return all jobs belonging to the authenticated user."""

    jobs = JobTrackerService.list_jobs(
        db=db,
        user_id=current_user.id,
        status=status,
        search=search,
        sort_by=sort_by,
        descending=descending,
    )
    return jobs


@router.get("/stats", response_model=JobStatsResponse)
def job_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JobStatsResponse:
    """Return dashboard statistics."""

    return JobTrackerService.get_job_stats(db=db, user_id=current_user.id)


@router.get("/{job_id}", response_model=JobApplicationResponse)
def get_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JobApplicationResponse:
    """Return one job application."""

    job = JobTrackerService.get_job(db=db, job_id=job_id, user_id=current_user.id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job application not found.",
        )
    return job


@router.get("/{job_id}/workspace")
def get_job_workspace(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Deterministic workspace header for an application.

    Returns the single recommended next action (a fixed decision tree over real
    completion state — never an AI decision), the non-dismissed insight cards
    (JD match gaps, resume analysis suggestions), and the dismissed insight keys
    for this user+application. Ownership-checked.
    """
    job = JobTrackerService.get_job(db=db, job_id=job_id, user_id=current_user.id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job application not found.",
        )
    payload = build_workspace_payload(db, current_user.id, job)
    return success_response(data=payload)


@router.post("/{job_id}/workspace/insights/{insight_key}/dismiss")
def dismiss_workspace_insight(
    job_id: int,
    insight_key: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Dismiss an insight card for this application so it does not reappear.

    Persists a user-scoped dismissal row; returning the updated dismissed list
    lets the client stay in sync without another round-trip.
    """
    job = JobTrackerService.get_job(db=db, job_id=job_id, user_id=current_user.id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job application not found.",
        )
    dismissed = dismiss_insight(db, current_user.id, job_id, insight_key)
    return success_response(data={"dismissed": dismissed})


@router.post("", response_model=JobApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_data: JobApplicationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JobApplicationResponse:
    """Create a new application."""

    return JobTrackerService.create_job(
        db=db,
        user_id=current_user.id,
        job_data=job_data,
    )


@router.put("/{job_id}", response_model=JobApplicationResponse)
def update_job(
    job_id: int,
    job_data: JobApplicationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JobApplicationResponse:
    """Update an existing application."""

    job = JobTrackerService.update_job(
        db=db,
        job_id=job_id,
        user_id=current_user.id,
        job_data=job_data,
    )
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job application not found.",
        )
    return job


@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete an application."""

    deleted = JobTrackerService.delete_job(db=db, job_id=job_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job application not found.",
        )

    return deleted_response(message="Job application deleted.")


