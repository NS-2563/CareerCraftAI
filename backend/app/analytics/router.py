from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.utils.response import success_response
from app.analytics.service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/history")
def get_snapshot_history(
    metric_type: str = Query(..., description="Metric type to retrieve history for"),
    limit: int = Query(100, ge=1, le=500),
    descending: bool = Query(False, description="Return newest snapshots first"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    snapshots = AnalyticsService.get_history(
        db=db,
        user_id=current_user.id,
        metric_type=metric_type,
        limit=limit,
        descending=descending,
    )

    items = [
        {
            "id": s.id,
            "metric_type": s.metric_type,
            "value": s.value,
            "recorded_at": s.recorded_at.isoformat() if s.recorded_at else None,
        }
        for s in snapshots
    ]

    return success_response(data={"items": items, "metric_type": metric_type})
