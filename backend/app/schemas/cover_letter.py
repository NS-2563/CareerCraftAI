from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any

class CoverLetterBase(BaseModel):
    """Base cover letter schema."""
    title: str = Field(default="Untitled Cover Letter")


class CoverLetterCreate(CoverLetterBase):
    """Schema for creating a new cover letter."""
    resume_id: Optional[int] = None
    job_application_id: Optional[int] = None
    content: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    job_description: Optional[str] = None
    tone: Optional[str] = Field(default="professional")
    template: Optional[str] = Field(default="modern")


class CoverLetterUpdate(BaseModel):
    """Schema for updating an existing cover letter."""
    title: Optional[str] = None
    resume_id: Optional[int] = None
    job_application_id: Optional[int] = None
    content: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    job_description: Optional[str] = None
    tone: Optional[str] = None
    template: Optional[str] = None


class CoverLetterResponse(BaseModel):
    """Schema for cover letter response."""
    id: int
    user_id: int
    resume_id: Optional[int] = None
    job_application_id: Optional[int] = None
    title: str
    content: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    job_description: Optional[str] = None
    tone: str = "professional"
    template: str = "modern"
    is_archived: bool = False
    version: int = 1
    ai_provider: Optional[str] = None
    model_name: Optional[str] = None
    generated_at: Optional[datetime] = None
    ats_coverage: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "protected_namespaces": (),
    }


class CoverLetterPreflightRequest(BaseModel):
    """Schema for the deterministic pre-flight generation check.

    Mirrors the inputs the generation endpoint consumes so the client can ask
    "which required inputs are missing?" before attempting an AI call.
    """
    resume_id: Optional[int] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    job_description: Optional[str] = None


class CoverLetterPreflightResponse(BaseModel):
    """Schema for the pre-flight check result."""
    ready: bool
    missing: List[str]


class CoverLetterDuplicateRequest(BaseModel):
    """Schema for duplicating a cover letter."""
    title: str = Field(default="Copy of Cover Letter")


class CoverLetterRenameRequest(BaseModel):
    """Schema for renaming a cover letter."""
    title: str = Field(..., min_length=1, max_length=255)


class CoverLetterGenerateRequest(BaseModel):
    """Schema for generating a cover letter with AI."""
    resume_id: Optional[int] = None
    job_title: str = Field(..., min_length=1)
    company_name: str = Field(..., min_length=1)
    job_description: Optional[str] = None
    tone: str = Field(default="professional")


class VersionRestoreRequest(BaseModel):
    """Schema for restoring a version."""
    version: int = Field(..., ge=1)


class CoverLetterAIEditsRequest(BaseModel):
    """Schema for AI editing a cover letter."""
    action: str = Field(..., description="Action: improve, rewrite, shorten, expand, grammar_fix, ats_optimize")
    content: Optional[str] = None


class CoverLetterSearchRequest(BaseModel):
    """Schema for searching cover letters."""
    query: str
    include_archived: bool = False