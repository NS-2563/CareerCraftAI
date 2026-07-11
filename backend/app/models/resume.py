from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import json

from app.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Resume data stored as JSON (using Text with JSON encoding)
    personal = Column(Text, default="{}")
    summary = Column(Text)
    experience = Column(Text, default="[]")
    education = Column(Text, default="[]")
    skills = Column(Text, default="[]")
    projects = Column(Text, default="[]")
    certifications = Column(Text, default="[]")
    languages = Column(Text, default="[]")
    interests = Column(Text, default="[]")
    references = Column(Text, default="[]")

    # Metadata
    name = Column(String(255), default="Untitled Resume")
    is_default = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    completed = Column(Boolean, default=False, nullable=False)

    # Versioning (placeholder)
    version = Column(Integer, default=1)
    version_history = Column(Text, default="[]")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="resumes")
    cover_letters = relationship("CoverLetter", back_populates="resume", cascade="all, delete-orphan")

    def _load_json(self, field):
        if field:
            try:
                return json.loads(field)
            except:
                return []
        return []

    def _save_json(self, data):
        if data is None:
            return "[]"
        try:
            return json.dumps(data)
        except:
            return "[]"

    @property
    def experience_list(self):
        return self._load_json(self.experience)

    @experience_list.setter
    def experience_list(self, value):
        self.experience = self._save_json(value)

    @property
    def education_list(self):
        return self._load_json(self.education)

    @education_list.setter
    def education_list(self, value):
        self.education = self._save_json(value)

    @property
    def skills_list(self):
        return self._load_json(self.skills)

    @skills_list.setter
    def skills_list(self, value):
        self.skills = self._save_json(value)

    @property
    def projects_list(self):
        return self._load_json(self.projects)

    @projects_list.setter
    def projects_list(self, value):
        self.projects = self._save_json(value)

    @property
    def personal_dict(self):
        return self._load_json(self.personal) if self.personal else {}

    @personal_dict.setter
    def personal_dict(self, value):
        self.personal = self._save_json(value)