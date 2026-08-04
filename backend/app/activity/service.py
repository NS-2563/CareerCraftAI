import logging

from sqlalchemy.orm import Session

from app.activity.models import ActivityEvent

logger = logging.getLogger(__name__)


class ActivityService:

    @staticmethod
    def log_event(
        db: Session,
        user_id: int,
        event_type: str,
        title: str,
        description: str = None,
        related_entity_type: str = None,
        related_entity_id: int = None,
        related_job_application_id: int = None,
    ) -> None:
        try:
            event = ActivityEvent(
                user_id=user_id,
                event_type=event_type,
                title=title,
                description=description,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                related_job_application_id=related_job_application_id,
            )
            db.add(event)
            db.commit()
        except Exception:
            logger.warning(
                "Failed to log activity event user_id=%s type=%s title=%s",
                user_id, event_type, title,
                exc_info=True,
            )

    @staticmethod
    def get_recent(
        db: Session,
        user_id: int,
        limit: int = 10,
    ) -> list[ActivityEvent]:
        return (
            db.query(ActivityEvent)
            .filter(ActivityEvent.user_id == user_id)
            .order_by(ActivityEvent.created_at.desc(), ActivityEvent.id.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def list_events(
        db: Session,
        user_id: int,
        event_type: str = None,
        job_application_id: int = None,
        limit: int = 200,
        offset: int = 0,
    ) -> tuple[list[ActivityEvent], int]:
        """Return a user's activity events with optional filters.

        Ordered newest-first. ``event_type`` filters to one event type;
        ``job_application_id`` filters to events linked to that application.
        Returns ``(items, total)`` where ``total`` is the filtered count.
        """
        query = db.query(ActivityEvent).filter(ActivityEvent.user_id == user_id)

        if event_type:
            query = query.filter(ActivityEvent.event_type == event_type)
        if job_application_id is not None:
            query = query.filter(
                ActivityEvent.related_job_application_id == job_application_id
            )

        total = query.count()
        items = (
            query
            .order_by(ActivityEvent.created_at.desc(), ActivityEvent.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return items, total
