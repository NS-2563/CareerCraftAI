from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import json

from app.database import Base


class CoverLetter(Base):
    """Cover letter model for storing user cover letters."""
    __tablename__ = "cover_letters"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=True)
    job_application_id = Column(
        Integer,
        ForeignKey("job_applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Content
    title = Column(String(255), default="Untitled Cover Letter")
    content = Column(Text)
    job_title = Column(String(255))
    company_name = Column(String(255))
    job_description = Column(Text)
    tone = Column(String(50), default="professional")

    # Generation metadata (set server-side at AI generation time only)
    ai_provider = Column(String(50), nullable=True)
    model_name = Column(String(100), nullable=True)
    generated_at = Column(DateTime(timezone=True), nullable=True)

    # Template
    template = Column(String(50), default="modern")

    # Status
    is_archived = Column(Boolean, default=False)

    # Versioning
    version = Column(Integer, default=1)
    version_history = Column(Text, default="[]")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="cover_letters")
    resume = relationship("Resume", back_populates="cover_letters")
    job_application = relationship("JobApplication")

    def _load_json(self, field):
        """Load JSON field."""
        if field:
            try:
                return json.loads(field)
            except:
                return []
        return []

    def _save_json(self, data):
        """Save data as JSON."""
        if data is None:
            return "[]"
        try:
            return json.dumps(data)
        except:
            return "[]"

    @property
    def version_history_list(self):
        """Get version history as list."""
        return self._load_json(self.version_history)

    @version_history_list.setter
    def version_history_list(self, value):
        """Set version history."""
        self.version_history = self._save_json(value)