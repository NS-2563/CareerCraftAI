from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    session_type = Column(String(50), nullable=False, default="practice", index=True)

    related_job_application_id = Column(
        Integer,
        ForeignKey("job_applications.id", ondelete="SET NULL"),
        nullable=True,
    )

    job_title = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    job_role_normalized = Column(String(255), nullable=True, index=True)
    skills = Column(Text, nullable=True)
    difficulty = Column(String(50), nullable=True)
    question_count = Column(Integer, nullable=False, default=5)

    questions = Column(Text, nullable=True)

    answers = Column(Text, nullable=True)

    overall_score = Column(Float, nullable=True)

    how_it_went = Column(Text, nullable=True)
    self_rated_confidence = Column(Float, nullable=True)
    questions_asked = Column(Text, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="interview_sessions")
