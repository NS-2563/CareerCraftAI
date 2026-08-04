from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type = Column(String(64), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)

    related_entity_type = Column(String(64), nullable=True)
    related_entity_id = Column(Integer, nullable=True)

    # When the event is linked to a job application (e.g. a communication message,
    # cover letter, JD match, or interview tied to an application), store the
    # application id so timeline entries can deep-link to the application's
    # workspace view regardless of the primary related entity.
    related_job_application_id = Column(Integer, nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
