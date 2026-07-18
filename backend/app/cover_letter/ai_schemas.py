from pydantic import BaseModel, Field
from typing import Optional


class GenerateCoverLetterRequest(BaseModel):
    """Schema for generating a cover letter with AI."""
    resume_id: Optional[int] = None
    job_title: str = Field(..., min_length=1)
    company_name: str = Field(..., min_length=1)
    job_description: Optional[str] = None
    tone: str = Field(default="professional")


class GenerateCoverLetterResponse(BaseModel):
    """Schema for cover letter generation response."""
    content: str


class AICoverLetterEditRequest(BaseModel):
    """Schema for AI editing a cover letter."""
    action: str = Field(..., description="Action: improve, rewrite, shorten, expand, grammar_fix, ats_optimize")
    content: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None


class AICoverLetterEditResponse(BaseModel):
    """Schema for AI cover letter edit response."""
    content: str