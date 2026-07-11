from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user

from app.models.user import User

from app.career.services.history_service import (
    get_history,
    get_report,
    delete_report,
    clear_history,
)

router = APIRouter(
    prefix="/career",
    tags=["Career History"],
)


@router.get("/history")
def history(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    ),
):
    """
    Return all saved career reports
    for the current user.
    """

    return get_history(
        db=db,
        user_id=current_user.id,
    )


@router.get("/history/{report_id}")
def history_detail(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    ),
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

    return report


@router.delete("/history/{report_id}")
def remove_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    ),
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

    return {
        "success": True,
        "message": "Career report deleted.",
    }


@router.delete("/history")
def remove_all_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    ),
):
    """
    Clear complete history.
    """

    deleted = clear_history(
        db=db,
        user_id=current_user.id,
    )

    return {
        "success": True,
        "deleted": deleted,
    }