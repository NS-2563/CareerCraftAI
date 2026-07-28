"""Central structured resume parser — deterministic rule-based extraction.

Phase 2C of Intelligent Resume Import.
Orchestrates section detection (Phase 2B) and dispatches to section-specific
deterministic parsers. Returns data in Resume Studio's canonical camelCase format.

Zero AI dependency. Designed for Phase 2D to add AI enrichment as a
non-destructive overlay.
"""
from typing import Any, Dict

from app.resume.services.section_detector import detect_sections
from app.resume.services.parsers.personal import parse_personal
from app.resume.services.parsers.summary import parse_summary
from app.resume.services.parsers.experience import parse_experience
from app.resume.services.parsers.education import parse_education
from app.resume.services.parsers.skills import parse_skills
from app.resume.services.parsers.projects import parse_projects
from app.resume.services.parsers.certifications import parse_certifications
from app.resume.services.parsers.languages import parse_languages
from app.resume.services.parsers.interests import parse_interests
from app.resume.services.parsers.references import parse_references


_LIST_SECTIONS = (
    "experience", "education", "skills", "projects",
    "certifications", "languages", "interests", "references",
)


def _normalize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Post-process the parsed result for consistency."""
    for key in _LIST_SECTIONS:
        if result.get(key) is None:
            result[key] = []

    if result.get("summary") is None:
        result["summary"] = ""

    return result


def parse_resume(raw_text: str) -> Dict[str, Any]:
    """Parse a full resume from raw text into structured data.

    The output dict uses the same camelCase keys that Resume Studio expects,
    making it directly compatible with resumeDataCompat.js and the frontend.

    Args:
        raw_text: Raw text extracted from a PDF resume.

    Returns:
        Dict with keys: personal, summary, experience, education, skills,
        projects, certifications, languages, interests, references,
        achievements (raw text, for intermediate use).
    """
    sections = detect_sections(raw_text)

    result: Dict[str, Any] = {
        "personal": parse_personal(sections.get("header", "")),
        "summary": parse_summary(sections.get("summary", "")),
        "experience": parse_experience(sections.get("experience", "")),
        "education": parse_education(sections.get("education", "")),
        "skills": parse_skills(sections.get("skills", "")),
        "projects": parse_projects(sections.get("projects", "")),
        "certifications": parse_certifications(sections.get("certifications", "")),
        "languages": parse_languages(sections.get("languages", "")),
        "interests": parse_interests(sections.get("interests", "")),
        "references": parse_references(sections.get("references", "")),
        "achievements": sections.get("achievements", ""),
    }

    result = _normalize_result(result)

    return result
