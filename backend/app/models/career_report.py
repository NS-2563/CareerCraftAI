from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class CareerReport(Base):
    __tablename__ = "career_reports"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    career_goal = Column(
        String(255),
        nullable=False,
    )

    readiness_score = Column(
        Integer,
        nullable=False,
        default=0,
    )

    best_match = Column(
        String(255),
        nullable=False,
        default="",
    )

    source = Column(
        String(20),
        nullable=False,
        default="ai",
    )

    report_json = Column(
        JSON,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="career_reports",
    )