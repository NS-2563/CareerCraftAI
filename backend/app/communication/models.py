from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CommunicationMessage(Base):
    __tablename__ = "communication_messages"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    message_type = Column(String(50), nullable=False)
    tone = Column(String(50), default="professional")

    direction = Column(String(10), nullable=False, default="outbound")
    sender_name = Column(String(255), nullable=True)
    sender_email = Column(String(255), nullable=True)

    # Provenance: 'ai_generated' when created by the AI /generate endpoint,
    # 'manual' when created by the manual create or log-inbound path.
    generation_method = Column(String(20), nullable=False, default="manual")

    recipient_name = Column(String(255), nullable=True)
    recipient_role = Column(String(255), nullable=True)
    recipient_company = Column(String(255), nullable=True)

    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=False)

    related_job_application_id = Column(Integer, ForeignKey("job_applications.id", ondelete="SET NULL"), nullable=True)
    related_resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)

    version = Column(Integer, default=1)
    version_history = Column(Text, default="[]")

    is_archived = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="communication_messages")
    related_job_application = relationship("JobApplication", foreign_keys=[related_job_application_id])
    related_resume = relationship("Resume", foreign_keys=[related_resume_id])


class CommunicationSuggestion(Base):
    __tablename__ = "communication_suggestions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_application_id = Column(Integer, ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False)

    suggestion_type = Column(String(50), nullable=False, default="follow_up_due")
    is_dismissed = Column(Boolean, default=False)
    is_actioned = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="communication_suggestions")
    job_application = relationship("JobApplication")

    __table_args__ = (
        UniqueConstraint("job_application_id", "suggestion_type", name="uq_job_suggestion_type"),
    )
