from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.database import Base


class RoadmapTaskStatus(Base):
    """User-set progress state for a Career Coach recommendation.

    One row per user per recommendation (keyed by normalized skill name), so a
    status survives regeneration of the underlying recommendation list. The
    status is entirely user-controlled and independent of the AI output.
    """

    __tablename__ = "roadmap_task_statuses"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "skill_key",
            name="uq_roadmap_task_status_user_skill_key",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill = Column(
        String(255),
        nullable=False,
        comment="Display casing of the recommendation skill",
    )
    skill_key = Column(
        String(255),
        nullable=False,
        comment="Lowercased/whitespace-normalized skill for identity matching",
    )
    status = Column(
        String(20),
        nullable=False,
        default="not_started",
    )
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
