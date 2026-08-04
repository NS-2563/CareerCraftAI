from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_active_user
from app.core.limiter import limiter
from app.models.user import User

from app.career.services.roadmap_task_service import (
    TASK_STATUSES,
    attach_task_statuses,
    get_task_status,
    set_task_status,
)
from app.career.services.history_service import get_history, save_report
from app.career.services.roadmap_service import generate_career_report
from app.activity.service import ActivityService
from app.activity.constants import EventType
from app.analytics.service import AnalyticsService

router = APIRouter(
    prefix="/api/career/roadmap",
    tags=["Career Roadmap"],
)


class TaskStatusRequest(BaseModel):
    status: str = Field(..., max_length=20)


def _latest_report(db: Session, user_id: int):
    """Return the newest saved report dict or None."""
    reports = get_history(db, user_id)
    if not reports:
        return None
    return reports[0].report_json or {}


@router.post("/refresh")
@limiter.limit(f"{settings.RATE_LIMIT_CAREER_COACH};{settings.RATE_LIMIT_CAREER_COACH_DAILY}")
def refresh_roadmap(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Re-run roadmap generation against current data.

    Rebuilds the generation inputs from the user's latest saved report (goal +
    the authoritative skills list) and regenerates with the live DB, so fresh
    JD matches, interview practice, and real interview logs feed the new
    recommendation set. The new report is saved as a new history row and
    returned with task statuses attached (matched by skill identity, so
    user-set statuses persist).
    """
    latest = _latest_report(db, current_user.id)
    if not latest:
        raise HTTPException(
            status_code=404,
            detail="No career report to refresh. Generate one first.",
        )

    skill_gap = latest.get("skill_gap") or {}
    existing = skill_gap.get("existing_skills") or []
    payload = {
        "goal": latest.get("career_goal") or "",
        "skills": ", ".join(
            str(s).strip() for s in existing if isinstance(s, str) and s.strip()
        ),
    }

    result = generate_career_report(
        payload,
        db=db,
        user_id=current_user.id,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", {}).get(
                "message", "Career report refresh failed."
            ),
        )

    report = result["data"]

    save_report(
        db=db,
        user_id=current_user.id,
        report=report,
        source=result.get("source", "ai"),
    )

    AnalyticsService.record_snapshot(
        db, current_user.id, "career_readiness",
        float(report.get("readiness_score", 0)),
    )

    ActivityService.log_event(
        db, current_user.id, EventType.CAREER_REPORT_GENERATED,
        title="Career report refreshed",
        description=report.get("career_goal") or "Career assessment",
        related_entity_type="career_report",
    )

    attach_task_statuses(db, current_user.id, report)

    return report


@router.get("/tasks/{task_id}/status")
def task_status_detail(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return one roadmap task's status, ownership-checked."""
    row = get_task_status(db, task_id, current_user.id)
    if row is None:
        raise HTTPException(status_code=404, detail="Roadmap task not found.")
    return {
        "task_id": row.id,
        "skill": row.skill,
        "status": row.status,
    }


@router.put("/tasks/{task_id}/status")
def task_status_update(
    task_id: int,
    body: TaskStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Set a roadmap task's status, ownership-checked."""
    if body.status not in TASK_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Allowed: {', '.join(TASK_STATUSES)}.",
        )

    row = set_task_status(db, task_id, current_user.id, body.status)
    if row is None:
        raise HTTPException(status_code=404, detail="Roadmap task not found.")

    return {
        "task_id": row.id,
        "skill": row.skill,
        "status": row.status,
    }
