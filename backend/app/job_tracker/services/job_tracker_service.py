from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from fastapi import HTTPException, status
from sqlalchemy import Integer, case, func, or_
from sqlalchemy.orm import Session

from app.models.job_application import JobApplication
from app.schemas.job_tracker import JobApplicationCreate, JobApplicationUpdate, JobStatsResponse, JobStatus
from app.activity.service import ActivityService
from app.activity.constants import EventType


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
            job_description=job_data.job_description,
            resume_id=job_data.resume_id,
        )

        db.add(job)
        db.commit()
        db.refresh(job)
        ActivityService.log_event(
            db, user_id, EventType.JOB_APPLICATION_CREATED,
            title="Job application created",
            description=f"{job_data.company} - {job_data.job_title}",
            related_entity_type="job_application",
            related_entity_id=job.id,
            related_job_application_id=job.id,
        )
        if job_data.job_description and job_data.job_description.strip():
            ActivityService.log_event(
                db, user_id, EventType.JOB_DESCRIPTION_ADDED,
                title="Job description added",
                description=f"{job_data.company} - {job_data.job_title}",
                related_entity_type="job_application",
                related_entity_id=job.id,
                related_job_application_id=job.id,
            )
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

        jd_was_empty = not (job.job_description or "").strip()

        for field, value in update_data.items():
            setattr(job, field, value)

        db.commit()
        db.refresh(job)

        if "job_description" in update_data and (job.job_description or "").strip():
            if jd_was_empty:
                ActivityService.log_event(
                    db, user_id, EventType.JOB_DESCRIPTION_ADDED,
                    title="Job description added",
                    description=f"{job.company} - {job.job_title}",
                    related_entity_type="job_application",
                    related_entity_id=job.id,
                    related_job_application_id=job.id,
                )
            else:
                ActivityService.log_event(
                    db, user_id, EventType.JOB_DESCRIPTION_UPDATED,
                    title="Job description updated",
                    description=f"{job.company} - {job.job_title}",
                    related_entity_type="job_application",
                    related_entity_id=job.id,
                    related_job_application_id=job.id,
                )

        if "status" in update_data:
            ActivityService.log_event(
                db, user_id, EventType.JOB_APPLICATION_STATUS_CHANGED,
                title="Application status changed",
                description=f"{job.company} - {job.job_title} → {update_data['status']}",
                related_entity_type="job_application",
                related_entity_id=job.id,
                related_job_application_id=job.id,
            )
        else:
            ActivityService.log_event(
                db, user_id, EventType.JOB_APPLICATION_UPDATED,
                title="Job application updated",
                description=f"{job.company} - {job.job_title}",
                related_entity_type="job_application",
                related_entity_id=job.id,
                related_job_application_id=job.id,
            )

        return job


    @staticmethod
    def delete_job(db: Session, job_id: int, user_id: int) -> bool:
        """Delete a job application if owned by the user.

        Related rows are cleaned up explicitly so behavior is consistent even on
        SQLite (which does not enforce ON DELETE actions without the FK pragma):
        - Cover letters keep existing, their job_application_id is nulled (SET NULL)
        - Persisted JD match results are removed (CASCADE)
        """
        job = JobTrackerService.get_job(db, job_id=job_id, user_id=user_id)
        if job is None:
            return False

        from app.models.cover_letter import CoverLetter
        from app.models.jd_match_result import JDMatchResult

        company = job.company
        job_title = job.job_title

        db.query(CoverLetter).filter(
            CoverLetter.job_application_id == job_id,
            CoverLetter.user_id == user_id,
        ).update({CoverLetter.job_application_id: None})
        db.query(JDMatchResult).filter(
            JDMatchResult.job_application_id == job_id,
            JDMatchResult.user_id == user_id,
        ).delete(synchronize_session=False)

        db.delete(job)
        db.commit()
        ActivityService.log_event(
            db, user_id, EventType.JOB_APPLICATION_DELETED,
            title="Job application deleted",
            description=f"{company} - {job_title}",
            related_entity_type="job_application",
            related_entity_id=job_id,
            related_job_application_id=job_id,
        )
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

