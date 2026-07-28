from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    resume_id = Column(
        Integer,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    resume_version = Column(Integer, nullable=False, default=1)

    source = Column(
        String(20),
        nullable=False,
        default="deterministic",
        comment="deterministic, ai, or full",
    )

    analysis_json = Column(
        JSON,
        nullable=False,
        comment="Full analysis result as JSON",
    )

    scores_json = Column(
        JSON,
        nullable=True,
        comment="Extracted score fields for quick lookup",
    )

    job_description_id = Column(
        Integer,
        ForeignKey("job_applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    is_stale = Column(
        Integer,
        nullable=False,
        default=0,
        comment="0 = fresh, 1 = stale (resume was updated after this analysis)",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="resume_analyses")
    resume = relationship("Resume", back_populates="resume_analyses")
    job_application = relationship("JobApplication", backref="resume_analyses")
