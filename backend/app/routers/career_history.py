from fastapi import APIRouter, Depends, HTTPException
from copy import deepcopy
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.career.services.analytics_service import get_analytics
from app.career.services.roadmap_task_service import attach_task_statuses

from app.career.services.history_service import (
    get_history,
    get_report,
    delete_report,
    clear_history,
)
from app.utils.response import deleted_response

router = APIRouter(
    prefix="/career",
    tags=["Career History"],
)


@router.get("/history")
def history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Return all saved career reports
    for the current user.
    """
    reports = get_history(
        db=db,
        user_id=current_user.id,
    )

    items = []
    for record in reports:
        report_json = deepcopy(record.report_json or {})
        attach_task_statuses(db, current_user.id, report_json)
        items.append({
            "id": record.id,
            "user_id": record.user_id,
            "career_goal": record.career_goal,
            "readiness_score": record.readiness_score,
            "best_match": record.best_match,
            "source": record.source,
            "created_at": record.created_at,
            "report_json": report_json,
        })

    return items

@router.get("/analytics")
def analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_analytics(
        db=db,
        user_id=current_user.id,
    )

@router.get("/history/{report_id}")
def history_detail(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Return one saved report.
    """
    report = get_report(
        db=db,
        report_id=report_id,
        user_id=current_user.id,
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Career report not found.",
        )

    report_json = deepcopy(report.report_json or {})
    attach_task_statuses(db, current_user.id, report_json)

    return {
        "id": report.id,
        "user_id": report.user_id,
        "career_goal": report.career_goal,
        "readiness_score": report.readiness_score,
        "best_match": report.best_match,
        "source": report.source,
        "created_at": report.created_at,
        "report_json": report_json,
    }


@router.delete("/history/{report_id}")
def remove_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete one report.
    """
    deleted = delete_report(
        db=db,
        report_id=report_id,
        user_id=current_user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Career report not found.",
        )

    return deleted_response(message="Career report deleted.")


@router.delete("/history")
def remove_all_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete all reports for the current user.
    """
    deleted = clear_history(
        db=db,
        user_id=current_user.id,
    )

    return {
        "success": True,
        "deleted": deleted,
    }