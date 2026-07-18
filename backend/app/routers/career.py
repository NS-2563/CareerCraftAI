from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user

from app.models.user import User

from app.career.services.roadmap_service import (
    generate_career_report,
)

from app.career.services.history_service import (
    save_report,
)

router = APIRouter()


@router.post("/career-coach")
def coach(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate a career report and automatically
    save it into the user's history.
    """

    result = generate_career_report(data)

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

    return report