from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.activity.service import ActivityService
from app.activity.models import ActivityEvent
from app.utils.response import success_response

router = APIRouter(prefix="/api/activity", tags=["Activity"])


def _serialize_event(e: ActivityEvent) -> dict:
    return {
        "id": e.id,
        "event_type": e.event_type,
        "title": e.title,
        "description": e.description,
        "related_entity_type": e.related_entity_type,
        "related_entity_id": e.related_entity_id,
        "related_job_application_id": e.related_job_application_id,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


@router.get("/recent")
def get_recent_activity(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=50),
):
    events = ActivityService.get_recent(db, user_id=current_user.id, limit=limit)
    items = [_serialize_event(e) for e in events]
    return success_response(data={"items": items})


@router.get("")
def get_activity_feed(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    event_type: str = Query(default=None, description="Filter to one event type"),
    job_application_id: int = Query(default=None, description="Filter to one job application"),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """Return the user's full chronological activity feed (newest-first).

    Supports filtering by event type and by job application so the timeline
    page can offer "only messages", "only this application", etc.
    """
    events, total = ActivityService.list_events(
        db=db,
        user_id=current_user.id,
        event_type=event_type,
        job_application_id=job_application_id,
        limit=limit,
        offset=offset,
    )
    items = [_serialize_event(e) for e in events]
    return success_response(
        data={
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(items) < total,
        }
    )
