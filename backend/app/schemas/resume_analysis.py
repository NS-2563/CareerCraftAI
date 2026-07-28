"""Schemas for persisted resume analysis records."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ResumeAnalysisResponse(BaseModel):
    id: int
    resume_id: int
    resume_version: int
    source: str
    analysis_json: Dict[str, Any]
    scores_json: Optional[Dict[str, Any]] = None
    job_description_id: Optional[int] = None
    is_stale: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeAnalysisListItem(BaseModel):
    id: int
    resume_id: int
    resume_version: int
    source: str
    is_stale: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeAnalysisHistoryResponse(BaseModel):
    analyses: List[ResumeAnalysisListItem]
    total: int
    current_version: int


class ResumeAnalysisStaleStatus(BaseModel):
    resume_id: int
    resume_version: int
    analysis_version: Optional[int] = None
    is_stale: bool = False
    has_cached: bool = False
    analysis_id: Optional[int] = None
    message: str = ""


class AnalysisCacheCheck(BaseModel):
    cached: bool
    stale: bool
    analysis: Optional[ResumeAnalysisResponse] = None


class ReAnalysisRequest(BaseModel):
    enable_ai: bool = Field(False, description="Enable AI deep analysis")
    force: bool = Field(False, description="Force re-analysis even if cache is fresh")
