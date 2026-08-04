from sqlalchemy import Column, Integer, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class JDMatchResult(Base):
    """Persisted resume-to-job-description match result.

    JD matching is normally stateless; when a request supplies a
    ``job_application_id`` the result is stored here so it can be shown on the
    application's detail view instead of being recomputed and lost.
    """

    __tablename__ = "jd_match_results"

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
        nullable=True,
        index=True,
    )
    resume_id = Column(
        Integer,
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
    )

    match_score = Column(Float, nullable=False)
    matched_skills = Column(Text, nullable=True)
    missing_skills = Column(Text, nullable=True)
    used_ai = Column(Boolean, nullable=False, default=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
