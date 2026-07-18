from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any, Union


# Resume field schemas
class PersonalInfo(BaseModel):
    """Personal information schema."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None


class ExperienceItem(BaseModel):
    """Experience entry schema."""
    id: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    current: Optional[bool] = False
    description: Optional[str] = None


class EducationItem(BaseModel):
    """Education entry schema."""
    id: Optional[str] = None
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None
    description: Optional[str] = None


class ProjectItem(BaseModel):
    """Project entry schema."""
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    technologies: Optional[List[str]] = None


class SkillItem(BaseModel):
    """Skill entry schema."""
    id: Optional[str] = None
    name: Optional[str] = None
    level: Optional[str] = None
    category: Optional[str] = None


class CertificationItem(BaseModel):
    """Certification entry schema."""
    id: Optional[str] = None
    name: Optional[str] = None
    issuer: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None


class LanguageItem(BaseModel):
    """Language entry schema."""
    id: Optional[str] = None
    language: Optional[str] = None
    proficiency: Optional[str] = None


class InterestItem(BaseModel):
    """Interest entry schema."""
    id: Optional[str] = None
    name: Optional[str] = None


class ReferenceItem(BaseModel):
    """Reference entry schema."""
    id: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    relationship: Optional[str] = None


# Resume schemas
class ResumeBase(BaseModel):
    name: str = Field(default="Untitled Resume")


class ResumeCreate(ResumeBase):
    """Schema for creating a new resume."""
    completed: Optional[bool] = Field(default=False)
    personal: Optional[PersonalInfo] = None
    summary: Optional[str] = None
    experience: Optional[List[ExperienceItem]] = Field(default_factory=list)
    education: Optional[List[EducationItem]] = Field(default_factory=list)
    skills: Optional[List[SkillItem]] = Field(default_factory=list)
    projects: Optional[List[ProjectItem]] = Field(default_factory=list)
    certifications: Optional[List[CertificationItem]] = Field(default_factory=list)
    languages: Optional[List[LanguageItem]] = Field(default_factory=list)
    interests: Optional[List[InterestItem]] = Field(default_factory=list)
    references: Optional[List[ReferenceItem]] = Field(default_factory=list)


class ResumeUpdate(BaseModel):
    """Schema for updating an existing resume."""
    name: Optional[str] = None
    completed: Optional[bool] = None
    personal: Optional[PersonalInfo] = None
    summary: Optional[str] = None
    experience: Optional[List[ExperienceItem]] = None
    education: Optional[List[EducationItem]] = None
    skills: Optional[List[SkillItem]] = None
    projects: Optional[List[ProjectItem]] = None
    certifications: Optional[List[CertificationItem]] = None
    languages: Optional[List[LanguageItem]] = None
    interests: Optional[List[InterestItem]] = None
    references: Optional[List[ReferenceItem]] = None


# Simple response schema that accepts raw values (string or dict)
class ResumeResponse(BaseModel):
    """Schema for resume response."""
    id: int
    user_id: int
    name: str
    completed: bool = False
    personal: Optional[Any] = None
    summary: Optional[str] = None
    experience: Optional[Any] = None
    education: Optional[Any] = None
    skills: Optional[Any] = None
    projects: Optional[Any] = None
    certifications: Optional[Any] = None
    languages: Optional[Any] = None
    interests: Optional[Any] = None
    references: Optional[Any] = None
    is_default: bool = False
    is_archived: bool = False
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ResumeDuplicateRequest(BaseModel):
    """Schema for duplicating a resume."""
    name: str = Field(default="Copy of Resume")


class ResumeRenameRequest(BaseModel):
    """Schema for renaming a resume."""
    name: str = Field(..., min_length=1, max_length=255)


class ResumeSearchRequest(BaseModel):
    """Schema for searching resumes."""
    query: str
    include_archived: bool = False


class VersionRestoreRequest(BaseModel):
    """Schema for restoring a version."""
    version: int = Field(..., ge=1)