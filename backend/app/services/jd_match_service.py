"""JD Match Service — orchestrates resume-to-job-description matching.

Combines deterministic and optional AI-powered semantic matching:
1. Validates JD text length
2. Normalizes resume data
3. Runs deterministic matching (reproducible, no AI dependency)
4. Optionally runs AI semantic matching
5. Assembles the final response
"""
import logging
from typing import Any, Dict, Optional

from app.analysis.deterministic.jd_matcher import compute_jd_match
from app.analysis.ai.jd_matcher import analyze_jd_semantic
from app.services.resume_service import ResumeService

logger = logging.getLogger(__name__)

_JD_MAX_LENGTH = 10000


def match_resume_to_jd(
    resume_data: Dict[str, Any],
    jd_text: str,
    enable_ai: bool = False,
) -> Dict[str, Any]:
    """Match a resume against a job description.

    Args:
        resume_data: Structured resume data (camelCase or snake_case)
        jd_text: Job description text
        enable_ai: Whether to run AI-powered semantic matching

    Returns:
        Complete match results
    """
    if not jd_text or not isinstance(jd_text, str):
        raise ValueError("Job description text is required")

    if len(jd_text) > _JD_MAX_LENGTH:
        raise ValueError(f"Job description exceeds {_JD_MAX_LENGTH} character limit")

    if not resume_data or not isinstance(resume_data, dict):
        raise ValueError("Resume data is required")

    logger.info(
        "Running JD match (jd_length=%d, enable_ai=%s)",
        len(jd_text),
        enable_ai,
    )

    det_result = compute_jd_match(resume_data, jd_text)

    ai_assessment = None
    if enable_ai:
        try:
            ai_assessment = analyze_jd_semantic(resume_data, jd_text, det_result)
            logger.info(
                "AI semantic matching completed: overall_match=%s",
                ai_assessment.get("overall_match"),
            )
        except Exception as e:
            logger.warning("AI semantic matching failed: %s", e)
            ai_assessment = {
                "overall_match": 0,
                "semantic_fit": "unavailable",
                "strengths": [],
                "gaps": [],
                "recommendations": [],
                "experience_fit_analysis": "AI analysis unavailable.",
                "skill_fit_analysis": "AI analysis unavailable.",
            }

    response = {
        "overall_match_score": det_result["overall_match_score"],
        "matched_skills": det_result["matched_skills"],
        "missing_skills": det_result["missing_skills"],
        "partial_matches": det_result["partial_matches"],
        "keyword_matches": det_result["keyword_matches"],
        "keyword_gaps": det_result["keyword_gaps"],
        "experience_relevance": det_result["experience_relevance"],
        "skill_relevance": det_result["skill_relevance"],
        "recommendations": det_result["recommendations"],
        "ai_semantic_assessment": ai_assessment,
        "deterministic": det_result["deterministic"],
    }

    return response


def load_resume_data(
    db,
    resume_id: Optional[int],
    user_id: int,
    resume_data: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Load resume data from DB or use inline data.

    Args:
        db: Database session
        resume_id: Resume ID to load (optional)
        user_id: User ID for ownership check
        resume_data: Inline resume data (optional)

    Returns:
        Resume data dictionary
    """
    if resume_data and isinstance(resume_data, dict):
        return resume_data

    if resume_id is not None:
        from app.services.resume_service import ResumeService
        resume = ResumeService.get_by_id(db, resume_id, user_id)

        import json
        return {
            "personal": json.loads(resume.personal) if isinstance(resume.personal, str) else (resume.personal or {}),
            "summary": resume.summary or "",
            "experience": json.loads(resume.experience) if isinstance(resume.experience, str) else (resume.experience or []),
            "education": json.loads(resume.education) if isinstance(resume.education, str) else (resume.education or []),
            "skills": json.loads(resume.skills) if isinstance(resume.skills, str) else (resume.skills or []),
            "projects": json.loads(resume.projects) if isinstance(resume.projects, str) else (resume.projects or []),
            "certifications": json.loads(resume.certifications) if isinstance(resume.certifications, str) else (resume.certifications or []),
            "languages": json.loads(resume.languages) if isinstance(resume.languages, str) else (resume.languages or []),
        }

    raise ValueError("Either resume_data or resume_id must be provided")
