from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_active_user
from app.core.limiter import limiter

from app.models.user import User
from app.schemas.career import CareerCoachRequest

from app.career.services.roadmap_service import (
    generate_career_report,
)

from app.career.services.history_service import (
    save_report,
)
from app.career.services.analytics_service import get_skill_gap_summary
from app.career.services.roadmap_task_service import attach_task_statuses
from app.activity.service import ActivityService
from app.activity.constants import EventType
from app.analytics.service import AnalyticsService

router = APIRouter(prefix="/api", tags=["Career"])


@router.post("/career-coach")
@limiter.limit(f"{settings.RATE_LIMIT_CAREER_COACH};{settings.RATE_LIMIT_CAREER_COACH_DAILY}")
def coach(
    request: Request,
    data: CareerCoachRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate a career report and automatically
    save it into the user's history.
    """

    result = generate_career_report(
        data.model_dump(),
        db=db,
        user_id=current_user.id,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get(
                "error",
                {}
            ).get(
                "message",
                "Career report generation failed."
            ),
        )

    report = result["data"]

    save_report(
        db=db,
        user_id=current_user.id,
        report=report,
        source=result.get("source", "ai"),
    )

    ActivityService.log_event(
        db, current_user.id, EventType.CAREER_REPORT_GENERATED,
        title="Career report generated",
        description=data.goal or "Career assessment",
        related_entity_type="career_report",
    )

    readiness_score = report.get("readiness_score", 0)
    AnalyticsService.record_snapshot(
        db, current_user.id, "career_readiness", float(readiness_score),
    )

    attach_task_statuses(db, current_user.id, report)

    return report


@router.get("/career/skill-gap-summary")
def skill_gap_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Return the user's most-frequently-missing skills across their stored
    JD match results.

    Computed purely from the current user's own JDMatchResult rows.  Returns
    an explicit insufficient-data response until at least the minimum sample
    size has been saved.  No external market data is involved.
    """
    return get_skill_gap_summary(db, current_user.id)