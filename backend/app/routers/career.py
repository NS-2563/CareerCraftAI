from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_active_user
from app.main import limiter

from app.models.user import User
from app.schemas.career import CareerCoachRequest

from app.career.services.roadmap_service import (
    generate_career_report,
)

from app.career.services.history_service import (
    save_report,
)

router = APIRouter()


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

    result = generate_career_report(data.model_dump())

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