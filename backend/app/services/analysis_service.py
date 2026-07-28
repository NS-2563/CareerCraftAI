"""Analysis service — orchestrates deterministic resume analysis.

This is the central orchestration layer. It:
1. Accepts structured resume data
2. Normalizes input safely
3. Runs deterministic analyzers
4. Aggregates results
5. Produces a structured AnalysisResult
6. Keeps deterministic analysis independent from AI
7. Provides extension points for future AI analysis

Future phases will add:
- AI deep analysis (Phase 3E)
- Hybrid scoring
- Persistence/caching (Phase 3I)
"""
import logging
from typing import Any, Dict, Optional

from app.analysis.deterministic.completeness import analyze_completeness
from app.analysis.deterministic.action_verbs import analyze_experience_action_verbs
from app.analysis.deterministic.metrics import analyze_metrics
from app.analysis.deterministic.ats_format import check_section_lengths, check_personal_info
from app.analysis.deterministic.keyword_density import analyze_keyword_density
from app.analysis.deterministic.bullet_quality import analyze_bullet_quality
from app.analysis.deterministic.section_balance import analyze_section_balance
from app.analysis.deterministic.summary_quality import analyze_summary_quality
from app.analysis.deterministic.ats_analysis import analyze_ats
from app.analysis.deterministic.skill_analysis import analyze_skills
from app.analysis.deterministic.strengths_weaknesses import analyze_strengths_weaknesses
from app.analysis.ai.deep_analysis import analyze_deep
from app.analysis.resume_quality import generate_quality_report
from app.services.recommendation_service import generate_recommendations

logger = logging.getLogger(__name__)


def _normalize_resume(resume: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize input resume data to canonical format.

    Handles both snake_case (backend) and camelCase (frontend) keys.
    """
    if not isinstance(resume, dict):
        logger.warning("Resume data is not a dict, using empty dict")
        return {}

    normalized = dict(resume)

    camel_to_snake = {
        "firstName": "first_name",
        "lastName": "last_name",
        "startDate": "start_date",
        "endDate": "end_date",
        "fieldOfStudy": "field_of_study",
        "credentialUrl": "url",
        "issueDate": "date",
    }

    personal = normalized.get("personal") or {}
    if isinstance(personal, dict):
        norm_personal = {}
        for k, v in personal.items():
            norm_personal[camel_to_snake.get(k, k)] = v
        normalized["personal"] = norm_personal

    for section in ("experience", "education", "projects", "certifications"):
        items = normalized.get(section) or []
        if isinstance(items, list):
            norm_items = []
            for item in items:
                if isinstance(item, dict):
                    norm_item = {}
                    for k, v in item.items():
                        norm_item[camel_to_snake.get(k, k)] = v
                    norm_items.append(norm_item)
                else:
                    norm_items.append(item)
            normalized[section] = norm_items

    if "firstName" in normalized or "lastName" in normalized:
        if "personal" not in normalized or not normalized["personal"]:
            normalized["personal"] = {}
        p = normalized["personal"]
        if "firstName" in normalized:
            p["first_name"] = normalized.pop("firstName")
        if "lastName" in normalized:
            p["last_name"] = normalized.pop("lastName")
        if "email" in normalized:
            p["email"] = normalized.pop("email")

    return normalized


def _compute_overall_quality_score(
    completeness: Dict[str, Any],
    action_verbs: Any,
    metrics: Dict[str, Any],
    bullet_quality: Dict[str, Any],
    section_balance: Dict[str, Any],
    summary_quality: Dict[str, Any],
) -> Dict[str, Any]:
    weights = {
        "completeness": 0.25,
        "action_verbs": 0.15,
        "metrics": 0.15,
        "summary_quality": 0.15,
        "bullet_quality": 0.15,
        "section_balance": 0.15,
    }

    completeness_score = completeness.get("overall_completeness_score", 0)

    if action_verbs and isinstance(action_verbs, dict):
        total = action_verbs.get("total_entries", 0)
        with_verbs = action_verbs.get("entries_with_verbs", 0)
        verb_score = round((with_verbs / total) * 100) if total > 0 else 0
    else:
        verb_score = 0

    metric_total = metrics.get("total_quantifiable", 0)
    metric_score = min(100, metric_total * 10)

    summary_score = summary_quality.get("summary_quality_score", 0)

    bullet_score = bullet_quality.get("bullet_quality_score", 0)

    balance_score = section_balance.get("balance_score", 0)

    raw_score = (
        completeness_score * weights["completeness"]
        + verb_score * weights["action_verbs"]
        + metric_score * weights["metrics"]
        + summary_score * weights["summary_quality"]
        + bullet_score * weights["bullet_quality"]
        + balance_score * weights["section_balance"]
    )

    overall_score = min(100, max(0, int(raw_score)))

    return {
        "overall_score": overall_score,
        "completeness_weighted": int(completeness_score * weights["completeness"]),
        "action_verb_weighted": int(verb_score * weights["action_verbs"]),
        "metrics_weighted": int(metric_score * weights["metrics"]),
        "summary_weighted": int(summary_score * weights["summary_quality"]),
        "bullet_weighted": int(bullet_score * weights["bullet_quality"]),
        "section_balance_weighted": int(balance_score * weights["section_balance"]),
        "weights_used": weights,
    }


def analyze_resume(
    resume: Dict[str, Any],
    enable_ai: bool = False,
    resume_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Run resume analysis (deterministic + optional AI deep analysis).

    Args:
        resume: Structured resume data (snake_case or camelCase)
        enable_ai: If True, runs optional AI-powered deep analysis
        resume_id: Optional resume DB ID for generating navigation URLs

    Returns:
        Analysis results with all component scores
    """
    normalized = _normalize_resume(resume)

    completeness = analyze_completeness(normalized)

    experience = normalized.get("experience") or []
    if not isinstance(experience, list):
        experience = []
    action_verbs = analyze_experience_action_verbs(experience)

    projects = normalized.get("projects") or []
    if not isinstance(projects, list):
        projects = []
    summary = normalized.get("summary") or ""
    metrics = analyze_metrics(experience, projects, summary)

    ats_lengths = check_section_lengths(normalized)
    ats_personal = check_personal_info(normalized)

    keywords = analyze_keyword_density(normalized)
    bullet_quality = analyze_bullet_quality(normalized)
    section_balance = analyze_section_balance(normalized)
    summary_text = normalized.get("summary") or ""
    summary_quality = analyze_summary_quality(summary_text)

    overall_quality_score = _compute_overall_quality_score(
        completeness=completeness,
        action_verbs=action_verbs if experience else None,
        metrics=metrics,
        bullet_quality=bullet_quality,
        section_balance=section_balance,
        summary_quality=summary_quality,
    )

    deterministic_result = {
        "completeness": completeness,
        "action_verbs": action_verbs if experience else None,
        "metrics": metrics,
        "ats_format": {
            "section_length_issues": ats_lengths["section_length_issues"],
            "personal_info": ats_personal,
            "details": ats_lengths["details"],
        },
        "keywords": keywords,
        "bullet_quality": bullet_quality,
        "section_balance": section_balance,
        "summary_quality": summary_quality,
        "overall_quality_score": overall_quality_score,
    }

    quality_report = generate_quality_report(
        resume=normalized,
        completeness=completeness,
        action_verbs=action_verbs if experience else None,
        metrics=metrics,
        ats_format={
            "section_length_issues": ats_lengths["section_length_issues"],
            "personal_info": ats_personal,
            "details": ats_lengths["details"],
        },
        keywords=keywords,
        bullet_quality=bullet_quality,
        section_balance=section_balance,
        summary_quality=summary_quality,
        overall_quality_score=overall_quality_score,
    )

    ats_result = analyze_ats(
        resume=normalized,
        completeness=completeness,
        action_verbs=action_verbs if experience else None,
        metrics=metrics,
        ats_format={
            "section_length_issues": ats_lengths["section_length_issues"],
            "personal_info": ats_personal,
            "details": ats_lengths["details"],
        },
        keywords=keywords,
        bullet_quality=bullet_quality,
        section_balance=section_balance,
        summary_quality=summary_quality,
    )

    skill_result = analyze_skills(normalized)

    sw_result = analyze_strengths_weaknesses(
        resume=normalized,
        completeness=completeness,
        action_verbs=action_verbs if experience else None,
        metrics=metrics,
        ats_format={
            "section_length_issues": ats_lengths["section_length_issues"],
            "personal_info": ats_personal,
            "details": ats_lengths["details"],
        },
        keywords=keywords,
        bullet_quality=bullet_quality,
        section_balance=section_balance,
        summary_quality=summary_quality,
        quality_report=quality_report,
        ats_analysis=ats_result,
        skill_analysis=skill_result,
    )

    if enable_ai:
        try:
            deep_result = analyze_deep(
                resume=normalized,
                completeness=completeness,
                ats_analysis=ats_result,
                skill_analysis=skill_result,
                strengths_weaknesses=sw_result,
            )
        except Exception as e:
            logger.warning("AI deep analysis failed: %s", e)
            deep_result = {
                "status": "error",
                "error": str(e),
                "ai_analysis": None,
                "hybrid": None,
            }
    else:
        deep_result = None

    analysis_result = {
        "deterministic": deterministic_result,
        "quality_report": quality_report,
        "ats_analysis": ats_result,
        "skill_analysis": skill_result,
        "strengths_weaknesses": sw_result,
        "deep_analysis": deep_result,
    }

    rec_result = generate_recommendations(analysis_result, resume_id=resume_id)
    analysis_result["recommendations"] = rec_result["recommendations"]
    analysis_result["total_recommendations"] = rec_result["total_count"]
    analysis_result["high_priority_recommendations"] = rec_result["high_priority_count"]

    return analysis_result
