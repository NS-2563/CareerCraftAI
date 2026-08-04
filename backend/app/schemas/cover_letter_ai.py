from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class GenerateCoverLetterRequest(BaseModel):
    """Schema for generating a cover letter with AI."""
    resume_id: Optional[int] = None
    job_title: str = Field(..., min_length=1)
    company_name: str = Field(..., min_length=1)
    job_description: Optional[str] = None
    tone: str = Field(default="professional")


class GenerateCoverLetterResponse(BaseModel):
    """Schema for cover letter generation response.

    ``content`` is the generated letter. ``ai_provider``/``model_name``/
    ``generated_at`` are the real provider metadata for this generation, and
    ``ats_coverage`` is the deterministic keyword-coverage count computed from
    the supplied job description and the generated text.
    """
    content: str
    ai_provider: Optional[str] = None
    model_name: Optional[str] = None
    generated_at: Optional[datetime] = None
    ats_coverage: Optional[dict] = None

    model_config = {"protected_namespaces": ()}


class AICoverLetterEditRequest(BaseModel):
    """Schema for AI editing a cover letter."""
    action: str = Field(..., description="Action: improve, rewrite, shorten, expand, grammar_fix, ats_optimize")
    content: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None


class AICoverLetterEditResponse(BaseModel):
    """Schema for AI cover letter edit response."""
    content: str
    ai_provider: Optional[str] = None
    model_name: Optional[str] = None
    generated_at: Optional[datetime] = None
    ats_coverage: Optional[dict] = None

    model_config = {"protected_namespaces": ()}