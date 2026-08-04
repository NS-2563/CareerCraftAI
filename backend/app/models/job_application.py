from sqlalchemy import Enum
from app.schemas.job_tracker import JobStatus
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)

    status = Column(
    Enum(JobStatus),
    nullable=False,
    default=JobStatus.WISHLIST,
    )

    source = Column(String(100), nullable=True)
    job_url = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    applied_date = Column(Date, nullable=True)
    deadline = Column(Date, nullable=True)

    job_description = Column(Text, nullable=True)
    resume_id = Column(
        Integer,
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Explicit user override for the conversation status
    # ("needs_reply" | "waiting" | "closed" | NULL = auto/derived).
    # Resolved via communication.conversation_status; terminal application
    # statuses always win over this value (see precedence rule there).
    conversation_status_override = Column(String(20), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )

    user = relationship(
        "User",
        back_populates="job_applications",
    )

    resume = relationship("Resume", foreign_keys=[resume_id])