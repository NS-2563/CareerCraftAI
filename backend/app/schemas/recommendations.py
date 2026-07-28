"""Actionable recommendation schemas for Phase 3J."""
from typing import Optional

from pydantic import BaseModel, Field


class ActionableRecommendation(BaseModel):
    id: str = Field(..., description="Unique identifier for this recommendation")
    priority: str = Field(..., pattern="^(high|medium|low)$")
    category: str = Field(..., description="e.g. experience, summary, skills, contact")
    description: str = Field(..., description="Human-readable description of the issue")
    evidence: str = Field(..., description="What the analysis found")
    recommended_fix: str = Field(..., description="What action to take")
    target_section: Optional[str] = Field(
        None, description="Wizard section ID to navigate to"
    )
    navigation_url: Optional[str] = Field(
        None,
        description="URL to navigate to for fixing this issue, e.g. /resume-studio?id=X&section=experience",
    )
    source_type: str = Field(
        ...,
        description="Origin of this finding: quality_issue, quality_warning, strength_weakness, ats_issue",
    )
    source_id: Optional[str] = Field(
        None, description="Reference to the original finding identifier"
    )


class RecommendationsResponse(BaseModel):
    recommendations: list[ActionableRecommendation] = []
    total_count: int = 0
    high_priority_count: int = 0
