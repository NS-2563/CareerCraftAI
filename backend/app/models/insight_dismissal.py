from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base


class InsightDismissal(Base):
    """User-scoped record of a dismissed workspace insight card.

    One row per (user, job application, insight key). When a row exists for a
    key, that insight card is hidden for the user on that application's
    workspace. Deleting the row (or the application) restores it.
    """

    __tablename__ = "insight_dismissals"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "job_application_id",
            "insight_key",
            name="uq_insight_dismissal_user_job_key",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    job_application_id = Column(
        Integer,
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Stable identifier of the insight (e.g. "jd_match_gaps", "resume_suggestions").
    insight_key = Column(String(64), nullable=False, index=True)

    dismissed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
