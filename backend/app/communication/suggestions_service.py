from datetime import datetime, timedelta, timezone
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, not_
from typing import List, Optional

from app.config import settings
from app.communication.models import CommunicationSuggestion, CommunicationMessage
from app.database import SessionLocal
from app.models.job_application import JobApplication
from app.schemas.job_tracker import JobStatus
from app.utils.exceptions import NotFoundException

logger = logging.getLogger(__name__)

_TERMINAL_STATUSES = {JobStatus.OFFER, JobStatus.ACCEPTED, JobStatus.REJECTED, JobStatus.WITHDRAWN}


def run_daily_suggestion_check(session_factory=SessionLocal):
    """Run the daily follow-up suggestion check in its own DB session.

    This is the shared entry point that the old in-process APScheduler job
    called. The HTTP trigger (POST /api/internal/run-daily-suggestions) runs
    the exact same logic via ``check_and_create_suggestions`` against a
    request-scoped session; any future non-HTTP trigger (a one-off script, a
    second process) can call this function instead. Both paths funnel into the
    same ``check_and_create_suggestions`` implementation.

    Returns the number of suggestions created. Unlike the old scheduler job,
    exceptions are re-raised (after logging) so the caller — an external
    scheduler with retry/alerting — knows the run failed.
    """
    db = session_factory()
    try:
        count = check_and_create_suggestions(db)
        if count:
            logger.info("Created %d follow-up suggestion(s)", count)
        return count
    except Exception:
        logger.exception("Follow-up suggestion check failed")
        raise
    finally:
        db.close()


def get_active_suggestions(db: Session, user_id: int) -> List[dict]:
    rows = (
        db.query(
            CommunicationSuggestion.id,
            CommunicationSuggestion.user_id,
            CommunicationSuggestion.job_application_id,
            CommunicationSuggestion.suggestion_type,
            CommunicationSuggestion.is_dismissed,
            CommunicationSuggestion.is_actioned,
            CommunicationSuggestion.created_at,
            JobApplication.company,
            JobApplication.job_title,
            JobApplication.updated_at,
        )
        .join(JobApplication, CommunicationSuggestion.job_application_id == JobApplication.id)
        .filter(
            CommunicationSuggestion.user_id == user_id,
            CommunicationSuggestion.is_dismissed == False,
        )
        .order_by(CommunicationSuggestion.created_at.desc())
        .all()
    )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    results = []
    for row in rows:
        updated = row.updated_at
        days_since = (now - updated.replace(tzinfo=None)).days if updated else 0
        results.append({
            "id": row.id,
            "user_id": row.user_id,
            "job_application_id": row.job_application_id,
            "suggestion_type": row.suggestion_type,
            "is_dismissed": row.is_dismissed,
            "is_actioned": row.is_actioned,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "job_company": row.company,
            "job_title": row.job_title,
            "days_since_update": days_since,
        })
    return results


def dismiss_suggestion(db: Session, suggestion_id: int, user_id: int) -> CommunicationSuggestion:
    suggestion = db.query(CommunicationSuggestion).filter(
        CommunicationSuggestion.id == suggestion_id,
        CommunicationSuggestion.user_id == user_id,
    ).first()
    if not suggestion:
        raise NotFoundException("CommunicationSuggestion", str(suggestion_id))
    suggestion.is_dismissed = True
    db.commit()
    db.refresh(suggestion)
    return suggestion


def mark_actioned(db: Session, suggestion_id: int, user_id: int) -> CommunicationSuggestion:
    suggestion = db.query(CommunicationSuggestion).filter(
        CommunicationSuggestion.id == suggestion_id,
        CommunicationSuggestion.user_id == user_id,
    ).first()
    if not suggestion:
        raise NotFoundException("CommunicationSuggestion", str(suggestion_id))
    suggestion.is_actioned = True
    db.commit()
    db.refresh(suggestion)
    return suggestion


def check_and_create_suggestions(db: Session):
    threshold_days = settings.SUGGESTION_FOLLOW_UP_DAYS
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=threshold_days)

    stale_jobs = (
        db.query(JobApplication)
        .filter(
            JobApplication.status.notin_(_TERMINAL_STATUSES),
            JobApplication.updated_at < cutoff,
        )
        .all()
    )

    created = 0
    for job in stale_jobs:
        existing = (
            db.query(CommunicationSuggestion)
            .filter(
                CommunicationSuggestion.job_application_id == job.id,
                CommunicationSuggestion.suggestion_type == "follow_up_due",
                CommunicationSuggestion.is_dismissed == False,
                CommunicationSuggestion.is_actioned == False,
            )
            .first()
        )
        if existing:
            continue

        suggestion = CommunicationSuggestion(
            user_id=job.user_id,
            job_application_id=job.id,
            suggestion_type="follow_up_due",
        )
        db.add(suggestion)
        created += 1

    if created:
        db.commit()

    return created
