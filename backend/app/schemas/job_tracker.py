from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    WISHLIST = "Wishlist"
    APPLIED = "Applied"
    INTERVIEW = "Interview"
    OFFER = "Offer"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    WITHDRAWN = "Withdrawn"


class JobApplicationBase(BaseModel):
    company: str
    job_title: str
    location: Optional[str] = None

    status: JobStatus = JobStatus.WISHLIST

    source: Optional[str] = None
    job_url: Optional[str] = None
    notes: Optional[str] = None

    applied_date: Optional[date] = None
    deadline: Optional[date] = None

    job_description: Optional[str] = None
    resume_id: Optional[int] = None


class JobApplicationCreate(JobApplicationBase):
    pass


class JobApplicationUpdate(BaseModel):
    company: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None

    status: Optional[JobStatus] = None

    source: Optional[str] = None
    job_url: Optional[str] = None
    notes: Optional[str] = None

    applied_date: Optional[date] = None
    deadline: Optional[date] = None

    job_description: Optional[str] = None
    resume_id: Optional[int] = None


class JobApplicationResponse(JobApplicationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class JobStatsResponse(BaseModel):
    total_applications: int
    wishlist: int
    applied: int
    interview: int
    offer: int
    accepted: int
    rejected: int
    withdrawn: int


class JdMatchSkillItem(BaseModel):
    name: str
    category: str = ""
    in_resume: bool = False
    in_jd: bool = True
    match_type: str = "exact"
    normalized_from: Optional[str] = None


class KeywordMatchInfo(BaseModel):
    matched_keywords: list[str] = []
    missing_keywords: list[str] = []
    jd_keywords: list[str] = []
    resume_keywords: list[str] = []
    match_count: int = 0
    total_count: int = 0
    match_percentage: float = 0.0


class ExperienceRelevanceInfo(BaseModel):
    score: int = 0
    relevant_years_demanded: Optional[int] = None
    relevant_years_supplied: Optional[int] = None
    matched_domains: list[str] = []
    assessment: str = ""


class SkillRelevanceInfo(BaseModel):
    matched_count: int = 0
    missing_count: int = 0
    total_jd_skills: int = 0
    total_resume_skills: int = 0
    match_percentage: float = 0.0
    by_category: dict[str, dict[str, int]] = {}


class AiSemanticAssessment(BaseModel):
    overall_match: int = 0
    semantic_fit: str = ""
    strengths: list[str] = []
    gaps: list[str] = []
    recommendations: list[str] = []
    experience_fit_analysis: str = ""
    skill_fit_analysis: str = ""


class DeterministicMatchResult(BaseModel):
    overall_score: int = 0
    skill_match: SkillRelevanceInfo = SkillRelevanceInfo()
    keyword_match: KeywordMatchInfo = KeywordMatchInfo()
    experience_relevance: ExperienceRelevanceInfo = ExperienceRelevanceInfo()


class JobDescriptionMatchRequest(BaseModel):
    jd_text: str = Field(..., min_length=1, max_length=10000, description="Job description text")
    resume_id: Optional[int] = Field(None, description="ID of saved resume to load")
    resume_data: Optional[dict[str, Any]] = Field(None, description="Inline resume data (camelCase or snake_case)")
    enable_ai: bool = Field(False, description="Enable AI-powered semantic matching")


class JobDescriptionMatchResponse(BaseModel):
    overall_match_score: int
    matched_skills: list[JdMatchSkillItem] = []
    missing_skills: list[JdMatchSkillItem] = []
    partial_matches: list[JdMatchSkillItem] = []
    keyword_matches: KeywordMatchInfo = KeywordMatchInfo()
    keyword_gaps: list[str] = []
    experience_relevance: ExperienceRelevanceInfo = ExperienceRelevanceInfo()
    skill_relevance: SkillRelevanceInfo = SkillRelevanceInfo()
    recommendations: list[str] = []
    ai_semantic_assessment: Optional[AiSemanticAssessment] = None
    deterministic: DeterministicMatchResult = DeterministicMatchResult()

