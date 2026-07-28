from pydantic import BaseModel, Field
from typing import Optional, List, Any


# Base request schemas
class GenerateSummaryRequest(BaseModel):
    """Request schema for generating a summary."""
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    experience: Optional[List[dict]] = None
    education: Optional[List[dict]] = None
    skills: Optional[List[dict]] = None
    projects: Optional[List[dict]] = None


class ImproveTextRequest(BaseModel):
    """Base request schema for improving text."""
    text: str = Field(..., min_length=1, max_length=10000)


class ImproveSummaryRequest(ImproveTextRequest):
    """Request schema for improving a summary."""
    pass


class ImproveExperienceRequest(ImproveTextRequest):
    """Request schema for improving experience description."""
    position: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=255)


class ImproveProjectRequest(ImproveTextRequest):
    """Request schema for improving project description."""
    name: Optional[str] = Field(None, max_length=255)


class SuggestSkillsRequest(BaseModel):
    """Request schema for suggesting skills."""
    current_skills: Optional[List[str]] = Field(default_factory=list)
    job_title: Optional[str] = Field(None, max_length=255)
    job_description: Optional[str] = Field(None, max_length=5000)


class AnalyzeResumeRequest(BaseModel):
    """Request schema for analyzing a resume."""
    resume: dict


# Response schemas
class GenerateSummaryResponse(BaseModel):
    """Response schema for generating a summary."""
    summary: str


class ImproveTextResponse(BaseModel):
    """Base response schema for improved text."""
    improved_text: str


class ImproveSummaryResponse(ImproveTextResponse):
    """Response schema for improving a summary."""
    pass


class ImproveExperienceResponse(ImproveTextResponse):
    """Response schema for improving experience description."""
    pass


class ImproveProjectResponse(ImproveTextResponse):
    """Response schema for improving project description."""
    pass


class SuggestSkillsResponse(BaseModel):
    """Response schema for suggesting skills."""
    skills: List[str]
    categories: Optional[dict] = None


class AnalyzeResumeResponse(BaseModel):
    """Response schema for analyzing a resume."""
    resume_score: Optional[int] = Field(None, ge=0, le=100)
    ats_score: Optional[int] = Field(None, ge=0, le=100)
    analysis_failed: bool = False
    suggestions: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)