"""Analysis request/response Pydantic schemas."""
import json

from pydantic import BaseModel, Field, field_validator
from typing import Any, Dict, List, Optional

from app.schemas.recommendations import ActionableRecommendation


class AnalysisRequest(BaseModel):
    resume: Dict[str, Any] = Field(..., description="Structured resume data in canonical format")
    enable_ai: bool = Field(False, description="Enable AI-powered deep analysis (requires GEMINI_API_KEY)")
    resume_id: Optional[int] = Field(None, description="Resume ID for generating navigation URLs in recommendations")

    @field_validator("resume")
    @classmethod
    def validate_resume_size(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        raw = json.dumps(v, default=str)
        if len(raw) > 500_000:
            raise ValueError("Resume data exceeds 500KB size limit")
        return v


class SectionPresence(BaseModel):
    present: bool
    score: Optional[int] = None
    entry_count: Optional[int] = None
    count: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    entries: Optional[List[Dict[str, Any]]] = None


class ContactInfo(BaseModel):
    fields_present: int = 0
    fields_total: int = 0
    score: int = 0
    has_email: bool = False
    has_phone: bool = False
    has_name: bool = False
    has_location: bool = False
    profile_present: int = 0
    profile_total: int = 0
    profile_score: int = 0
    has_linkedin: bool = False
    has_github: bool = False
    has_website: bool = False


class CompletenessResult(BaseModel):
    overall_completeness_score: int
    section_presence: Dict[str, bool]
    section_completeness: Dict[str, SectionPresence]
    contact: ContactInfo
    summary_word_count: int


class ActionVerbEntry(BaseModel):
    has_action_verb: bool
    verb_count: int
    verbs: List[str]


class ActionVerbResult(BaseModel):
    total_entries: int
    entries_with_verbs: int
    entries_without_verbs: int
    all_verbs: List[str]
    entry_details: List[ActionVerbEntry]


class MetricsResult(BaseModel):
    percentages: List[str]
    currency_values: List[str]
    numbers: List[str]
    time_metrics: List[str]
    magnitude_words: List[str]
    total_quantifiable: int


class AtsSectionLengths(BaseModel):
    summary: Dict[str, Any]
    short_experience_entries: int


class AtsPersonalInfo(BaseModel):
    has_name: bool
    has_email: bool
    has_phone: bool
    has_location: bool
    missing_fields: List[str]
    ats_complete: bool


class AtsFormatResult(BaseModel):
    section_length_issues: int
    personal_info: AtsPersonalInfo
    details: AtsSectionLengths


class KeywordDensityResult(BaseModel):
    total_words: int
    keywords_found: Dict[str, bool]
    keyword_count: int
    keyword_density: float
    matched_keywords: List[str]
    missing_common_keywords: List[str]


class BulletQualityResult(BaseModel):
    bullet_quality_score: int
    total_bullets: int
    entries_with_data: int
    entries_missing_descriptions: int
    bullets_with_verb: int
    verb_ratio: float
    bullets_with_period: int
    period_ratio: float
    bullets_too_short: int
    bullets_too_long: int


class SectionBalanceResult(BaseModel):
    section_word_counts: Dict[str, int]
    total_words: int
    section_percentages: Dict[str, float]
    present_sections: List[str]
    balance_issues: List[str]
    dominant_section: Optional[str] = None
    balance_score: int
    section_count: int


class SummaryQualityResult(BaseModel):
    present: bool
    word_count: int
    length_grade: str
    has_action_verbs: bool
    action_verbs_found: List[str]
    has_metrics: bool
    metrics: Dict[str, int]
    keyword_count: int
    keywords_found: List[str]
    summary_quality_score: int


class OverallQualityScore(BaseModel):
    overall_score: int
    completeness_weighted: int
    action_verb_weighted: int
    metrics_weighted: int
    summary_weighted: int
    bullet_weighted: int
    section_balance_weighted: int
    weights_used: Dict[str, float]


class DeterministicAnalysis(BaseModel):
    """All deterministic analysis results for a resume."""
    completeness: CompletenessResult
    action_verbs: Optional[ActionVerbResult] = None
    metrics: MetricsResult
    ats_format: AtsFormatResult
    keywords: KeywordDensityResult
    bullet_quality: BulletQualityResult
    section_balance: SectionBalanceResult
    summary_quality: SummaryQualityResult
    overall_quality_score: OverallQualityScore


class QualityFinding(BaseModel):
    type: str  # "issue", "warning", "strength"
    section: str
    message: str
    details: Dict[str, Any] = {}


class SectionQuality(BaseModel):
    score: int
    issues: List[str] = []
    warnings: List[str] = []
    strengths: List[str] = []


class ResumeLengthInfo(BaseModel):
    total_words: int
    grade: str
    recommendation: str


class QualityReport(BaseModel):
    overall_score: int
    overall_status: str
    total_issues: int
    total_warnings: int
    total_strengths: int
    issues: List[QualityFinding] = []
    warnings: List[QualityFinding] = []
    strengths: List[QualityFinding] = []
    sections: Dict[str, SectionQuality]
    resume_length: ResumeLengthInfo


class SkillDetail(BaseModel):
    name: str
    original_name: str
    category_key: str
    category_label: str
    source: str
    normalized: bool = False
    confidence: str = "high"
    level: str = ""
    user_category: str = ""


class CategorizedSkills(BaseModel):
    programming_languages: List[SkillDetail] = []
    frameworks: List[SkillDetail] = []
    databases: List[SkillDetail] = []
    cloud_technologies: List[SkillDetail] = []
    tools: List[SkillDetail] = []
    technologies: List[SkillDetail] = []
    soft_skills: List[SkillDetail] = []


class SkillAnalysisResult(BaseModel):
    all_skills: List[SkillDetail]
    categorized: CategorizedSkills
    skill_count: int
    explicit_count: int
    implicit_count: int
    certification_count: int = 0
    certification_derived: List[SkillDetail] = []
    normalized_skills: Dict[str, str] = {}
    uncategorized: List[str] = []
    sources: Dict[str, int]


class AtsComponentDetail(BaseModel):
    score: int
    max_score: int = 100
    issues: List[str] = []
    strengths: List[str] = []
    details: Dict[str, Any] = {}


class AtsComponentScores(BaseModel):
    structure: int
    keywords: int
    action_verbs: int
    quantified_impact: int
    contact_info: int


class AtsDateConsistency(BaseModel):
    dominant_format: Optional[str] = None
    issues: List[str] = []


class AtsBulletConsistency(BaseModel):
    std_dev: float = 0.0
    grade: str = "insufficient_data"


class AtsAnalysisResult(BaseModel):
    overall_ats_score: int
    component_scores: AtsComponentScores
    component_details: Dict[str, AtsComponentDetail]
    risk_level: str
    risk_factors: List[str] = []
    recommendations: List[str] = []
    ats_issues: List[Dict[str, Any]] = []
    ats_warnings: List[Dict[str, Any]] = []
    ats_strengths: List[Dict[str, Any]] = []
    date_format_consistency: AtsDateConsistency
    bullet_consistency: AtsBulletConsistency


class StrengthWeaknessItem(BaseModel):
    type: str  # "strength" or "weakness"
    category: str
    title: str
    description: str
    severity: str  # "low", "medium", "high"
    priority: Optional[str] = None  # only for weaknesses
    evidence: Dict[str, Any] = {}
    source: str = "deterministic"


class StrengthsWeaknessesResult(BaseModel):
    strengths: List[StrengthWeaknessItem] = []
    weaknesses: List[StrengthWeaknessItem] = []
    strength_count: int = 0
    weakness_count: int = 0
    top_priorities: List[str] = []


class AiDimensionDetail(BaseModel):
    score: int = 0
    analysis: str = ""
    strengths: List[str] = []
    issues: List[str] = []
    suggestions: List[str] = []


class AiExperienceEntry(BaseModel):
    relevance: str = ""
    suggestions: List[str] = []


class AiAchievementExample(BaseModel):
    text: str = ""
    impact_level: str = ""
    suggestion: str = ""


class AiSkillSuggestion(BaseModel):
    skill: str = ""
    reason: str = ""


class AiSkillSuggestions(BaseModel):
    current_strengths: List[str] = []
    gaps: List[str] = []
    recommended: List[AiSkillSuggestion] = []


class AiRecommendation(BaseModel):
    priority: str = "medium"
    category: str = "general"
    action: str = ""
    details: str = ""
    target_section: str = ""


class AiWeaknessItem(BaseModel):
    category: str = "general"
    title: str = ""
    description: str = ""
    priority: str = "medium"
    suggestion: str = ""


class AiStrengthItem(BaseModel):
    category: str = "general"
    title: str = ""
    description: str = ""


class AiDeepAnalysis(BaseModel):
    content_quality: AiDimensionDetail
    summary_quality: AiDimensionDetail
    experience_relevance: AiDimensionDetail = AiDimensionDetail()
    achievement_impact: AiDimensionDetail
    strengths: List[AiStrengthItem] = []
    weaknesses: List[AiWeaknessItem] = []
    skill_suggestions: AiSkillSuggestions = AiSkillSuggestions()
    recommendations: List[AiRecommendation] = []
    overall_assessment: str = ""


class HybridStrengthWeakness(BaseModel):
    source: str  # "deterministic" or "ai"
    type: str = "strength"
    category: str = ""
    title: str = ""
    description: str = ""
    severity: str = "medium"
    priority: Optional[str] = None
    evidence: Dict[str, Any] = {}
    suggestion: Optional[str] = None


class HybridResult(BaseModel):
    strengths: List[HybridStrengthWeakness] = []
    weaknesses: List[HybridStrengthWeakness] = []
    overall_assessment: str = ""


class DeepAnalysisResult(BaseModel):
    status: str = "error"  # "success", "error"
    error: Optional[str] = None
    ai_analysis: Optional[AiDeepAnalysis] = None
    hybrid: Optional[HybridResult] = None


class AnalysisResponse(BaseModel):
    """Top-level analysis response."""
    status: str = "success"
    analyzed_at: str
    deterministic: DeterministicAnalysis
    quality_report: Optional[QualityReport] = None
    ats_analysis: Optional[AtsAnalysisResult] = None
    skill_analysis: Optional[SkillAnalysisResult] = None
    strengths_weaknesses: Optional[StrengthsWeaknessesResult] = None
    deep_analysis: Optional[DeepAnalysisResult] = None
    recommendations: List[ActionableRecommendation] = []
    total_recommendations: int = 0
    high_priority_recommendations: int = 0
