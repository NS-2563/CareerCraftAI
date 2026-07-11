from pydantic import BaseModel, Field
from typing import Optional, List, Any


# Base request schemas
class GenerateSummaryRequest(BaseModel):
    """Request schema for generating a summary."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    experience: Optional[List[dict]] = None
    education: Optional[List[dict]] = None
    skills: Optional[List[dict]] = None
    projects: Optional[List[dict]] = None


class ImproveTextRequest(BaseModel):
    """Base request schema for improving text."""
    text: str = Field(..., min_length=1)


class ImproveSummaryRequest(ImproveTextRequest):
    """Request schema for improving a summary."""
    pass


class ImproveExperienceRequest(ImproveTextRequest):
    """Request schema for improving experience description."""
    position: Optional[str] = None
    company: Optional[str] = None


class ImproveProjectRequest(ImproveTextRequest):
    """Request schema for improving project description."""
    name: Optional[str] = None


class SuggestSkillsRequest(BaseModel):
    """Request schema for suggesting skills."""
    current_skills: Optional[List[str]] = Field(default_factory=list)
    job_title: Optional[str] = None
    job_description: Optional[str] = None


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
    resume_score: int = Field(..., ge=0, le=100)
    ats_score: int = Field(..., ge=0, le=100)
    suggestions: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)