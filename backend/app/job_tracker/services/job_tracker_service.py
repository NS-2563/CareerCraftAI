from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from sqlalchemy import Integer, case, func, or_
from sqlalchemy.orm import Session

from app.models.job_application import JobApplication
from app.schemas.job_tracker import JobApplicationCreate, JobApplicationUpdate, JobStatsResponse, JobStatus


SortBy = Literal["created_at", "company", "job_title", "applied_date"]



class JobTrackerService:
    """Service layer for Job Tracker (job application CRUD and stats)."""

    @staticmethod
    def create_job(
        db: Session,
        user_id: int,
        job_data: JobApplicationCreate,
    ) -> JobApplication:
        """Create a new job application associated with the given user."""
        # Backend validation: deadline must be on or after applied_date when both are provided.
        if (
            job_data.applied_date is not None
            and job_data.deadline is not None
            and job_data.deadline < job_data.applied_date
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deadline must be on or after the applied date.",
            )

        job = JobApplication(
            user_id=user_id,
            company=job_data.company,
            job_title=job_data.job_title,
            location=job_data.location,
            status=job_data.status,
            source=job_data.source,
            job_url=job_data.job_url,
            notes=job_data.notes,
            applied_date=job_data.applied_date,
            deadline=job_data.deadline,
        )

        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_job(
        db: Session,
        job_id: int,
        user_id: int,
    ) -> Optional[JobApplication]:
        """Return a single job application belonging to the user, or None."""
        return (
            db.query(JobApplication)
            .filter(JobApplication.id == job_id, JobApplication.user_id == user_id)
            .first()
        )

    @staticmethod
    def list_jobs(
        db: Session,
        user_id: int,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: SortBy = "created_at",
        descending: bool = True,
    ) -> List[JobApplication]:
        """List the current user's jobs with optional filtering, searching, and sorting."""

        # Prevent arbitrary SQL injection by only allowing known sort fields.
        sort_field_map = {
            "created_at": JobApplication.created_at,
            "company": JobApplication.company,
            "job_title": JobApplication.job_title,
            "applied_date": JobApplication.applied_date,
        }
        sort_column = sort_field_map[sort_by]

        query = db.query(JobApplication).filter(JobApplication.user_id == user_id)

        if status is not None:
            # JobStatus is stored as Enum(JobStatus) in SQLAlchemy.
            # Accept both enum values and strings.
            query = query.filter(JobApplication.status == status)

        if search:
            # Case-insensitive search over company, job_title, location.
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    JobApplication.company.ilike(pattern),
                    JobApplication.job_title.ilike(pattern),
                    JobApplication.location.ilike(pattern),
                )
            )

        order_expr = sort_column.desc() if descending else sort_column.asc()
        query = query.order_by(order_expr)

        return query.all()

    @staticmethod
    def update_job(
        db: Session,
        job_id: int,
        user_id: int,
        job_data: JobApplicationUpdate,
    ) -> Optional[JobApplication]:
        """Update only explicitly-provided fields for a user's job application."""
        job = JobTrackerService.get_job(db, job_id=job_id, user_id=user_id)
        if job is None:
            return None

        update_data: Dict[str, Any] = job_data.model_dump(exclude_unset=True)

        # Backend validation: deadline must be on or after applied_date when both are provided.
        # JobApplicationUpdate may exclude unset fields; model_dump(exclude_unset=True) contains only what the client sent.
        if "applied_date" in update_data or "deadline" in update_data:
            applied_date = update_data.get("applied_date", job.applied_date)
            deadline = update_data.get("deadline", job.deadline)
            if applied_date is not None and deadline is not None and deadline < applied_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Deadline must be on or after the applied date.",
                )

        for field, value in update_data.items():
            setattr(job, field, value)

        db.commit()
        db.refresh(job)
        return job


    @staticmethod
    def delete_job(db: Session, job_id: int, user_id: int) -> bool:
        """Delete a job application if owned by the user."""
        job = JobTrackerService.get_job(db, job_id=job_id, user_id=user_id)
        if job is None:
            return False

        db.delete(job)
        db.commit()
        return True

    @staticmethod
    def get_job_stats(db: Session, user_id: int) -> JobStatsResponse:
        """Return dashboard statistics counts for the user's job applications."""

        # Count directly in SQL with conditional aggregation.
        # Enum values are compared by their string representation (as stored by SQLAlchemy/Enum).
        total = func.count(JobApplication.id).label("total")

        wishlist = func.sum((JobApplication.status == JobStatus.WISHLIST).cast(
            Integer
        )).label("wishlist")
        applied = func.sum((JobApplication.status == JobStatus.APPLIED).cast(Integer)).label("applied")
        interview = func.sum((JobApplication.status == JobStatus.INTERVIEW).cast(Integer)).label("interview")
        offer = func.sum((JobApplication.status == JobStatus.OFFER).cast(Integer)).label("offer")
        accepted = func.sum((JobApplication.status == JobStatus.ACCEPTED).cast(Integer)).label("accepted")
        rejected = func.sum((JobApplication.status == JobStatus.REJECTED).cast(Integer)).label("rejected")
        withdrawn = func.sum((JobApplication.status == JobStatus.WITHDRAWN).cast(Integer)).label("withdrawn")

        row = (
            db.query(wishlist, applied, interview, offer, accepted, rejected, withdrawn, total)
            .filter(JobApplication.user_id == user_id)
            .one()
        )

        # row order matches selected columns: (wishlist, applied, interview, offer, accepted, rejected, withdrawn, total)
        return JobStatsResponse(
            total_applications=int(row.total or 0),
            wishlist=int(row.wishlist or 0),
            applied=int(row.applied or 0),
            interview=int(row.interview or 0),
            offer=int(row.offer or 0),
            accepted=int(row.accepted or 0),
            rejected=int(row.rejected or 0),
            withdrawn=int(row.withdrawn or 0),
        )

