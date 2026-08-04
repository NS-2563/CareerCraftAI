from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.utils.response import success_response
from app.dashboard.service import DashboardService
from app.dashboard.health_score import compute_career_health_score
from app.dashboard.milestones import detect_milestones

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_dashboard_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    summary = DashboardService.get_summary(db, current_user.id)
    return success_response(data=summary)


@router.get("/health-score")
def get_health_score(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Disclosed, reproducible Career Health Score over real sub-metrics only.
    Explicitly "not enough data yet" when too few sub-metrics exist."""
    score = compute_career_health_score(db, current_user.id)
    return success_response(data=score)


@router.get("/milestones")
def get_milestones(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Achievement milestones derived from real Activity Log events only."""
    milestones = detect_milestones(db, current_user.id)
    return success_response(data={"milestones": milestones})
