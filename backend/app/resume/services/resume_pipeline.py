"""End-to-end resume parsing pipeline.

Phase 2D — full deterministic + AI enrichment pipeline.

Flow:
  Raw Text → Section Detection → Deterministic Parsing → AI Enrichment
  → Merge → Normalize → Pydantic Validation

All AI calls have graceful fallback: failures fall through to
deterministic-only results. The pipeline never raises for AI errors.
"""
import logging
from typing import Any, Dict, Optional, Tuple

from app.resume.services.section_detector import detect_sections
from app.resume.services.structured_parser import parse_resume
from app.resume.services.ai_parser import enrich_deterministic_with_ai
from app.schemas.resume import (
    ResumeCreate,
    PersonalInfo,
    ExperienceItem,
    EducationItem,
    SkillItem,
    ProjectItem,
    CertificationItem,
    LanguageItem,
    InterestItem,
    ReferenceItem,
)

logger = logging.getLogger(__name__)

# Mapping from camelCase (pipeline output) to snake_case (Pydantic schemas)
_CAMEL_TO_SNAKE = {
    "firstName": "first_name",
    "lastName": "last_name",
    "fieldOfStudy": "field_of_study",
    "startDate": "start_date",
    "endDate": "end_date",
    "liveDemo": "live_url",
    "techStack": "technologies",
    "issueDate": "date",
    "credentialUrl": "url",
}

_SNAKE_TO_CAMEL = {v: k for k, v in _CAMEL_TO_SNAKE.items()}


def _camel_to_snake(data: Any) -> Any:
    """Convert camelCase keys to snake_case for Pydantic schemas."""
    if isinstance(data, dict):
        return {_CAMEL_TO_SNAKE.get(k, k): _camel_to_snake(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_camel_to_snake(item) for item in data]
    return data


def _snake_to_camel(data: Any) -> Any:
    """Convert snake_case keys back to camelCase for frontend."""
    if isinstance(data, dict):
        return {_SNAKE_TO_CAMEL.get(k, k): _snake_to_camel(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_snake_to_camel(item) for item in data]
    return data


def _build_resume_create(
    parsed: Dict[str, Any],
    resume_name: str,
    raw_text: str,
) -> Tuple[ResumeCreate, Dict[str, Any], Dict[str, Any]]:
    """Build a ResumeCreate schema from parsed data.

    Also returns source metadata and raw_text for storage.

    Returns:
        Tuple of (ResumeCreate, source_metadata, enriched_data)
    """
    # Personal info
    personal_snake = _camel_to_snake(parsed.get("personal", {}))
    try:
        personal = PersonalInfo(**personal_snake) if personal_snake else None
    except Exception as e:
        logger.warning("Personal info schema validation failed: %s", str(e))
        personal = None

    # Experience
    exp_snake = _camel_to_snake(parsed.get("experience", []))
    try:
        experience = [ExperienceItem(**e) for e in exp_snake] if exp_snake else []
    except Exception as e:
        logger.warning("Experience schema validation failed: %s", str(e))
        experience = []

    # Education
    edu_snake = _camel_to_snake(parsed.get("education", []))
    try:
        education = [EducationItem(**e) for e in edu_snake] if edu_snake else []
    except Exception as e:
        logger.warning("Education schema validation failed: %s", str(e))
        education = []

    # Skills
    skills_snake = _camel_to_snake(parsed.get("skills", []))
    try:
        skills = [SkillItem(**s) for s in skills_snake] if skills_snake else []
    except Exception as e:
        logger.warning("Skills schema validation failed: %s", str(e))
        skills = []

    # Projects — also handle title→name and techStack string→list
    proj_snake = _camel_to_snake(parsed.get("projects", []))
    for p in proj_snake:
        if "title" in p and "name" not in p:
            p["name"] = p.pop("title")
        if isinstance(p.get("technologies"), str):
            p["technologies"] = [t.strip() for t in p["technologies"].split(",") if t.strip()]
    try:
        projects = [ProjectItem(**p) for p in proj_snake] if proj_snake else []
    except Exception as e:
        logger.warning("Projects schema validation failed: %s", str(e))
        projects = []

    # Certifications
    cert_snake = _camel_to_snake(parsed.get("certifications", []))
    try:
        certifications = [CertificationItem(**c) for c in cert_snake] if cert_snake else []
    except Exception as e:
        logger.warning("Certifications schema validation failed: %s", str(e))
        certifications = []

    # Languages
    lang_snake = _camel_to_snake(parsed.get("languages", []))
    try:
        languages = [LanguageItem(**l) for l in lang_snake] if lang_snake else []
    except Exception as e:
        logger.warning("Languages schema validation failed: %s", str(e))
        languages = []

    # Interests
    interests_snake = _camel_to_snake(parsed.get("interests", []))
    try:
        interests = [InterestItem(**i) for i in interests_snake] if interests_snake else []
    except Exception as e:
        logger.warning("Interests schema validation failed: %s", str(e))
        interests = []

    # References
    refs_snake = _camel_to_snake(parsed.get("references", []))
    try:
        references = [ReferenceItem(**r) for r in refs_snake] if refs_snake else []
    except Exception as e:
        logger.warning("References schema validation failed: %s", str(e))
        references = []

    summary = parsed.get("summary", "")

    resume_create = ResumeCreate(
        name=resume_name[:255],
        completed=False,
        personal=personal,
        summary=summary[:50000] if summary else None,
        experience=experience,
        education=education,
        skills=skills,
        projects=projects,
        certifications=certifications,
        languages=languages,
        interests=interests,
        references=references,
    )

    source_meta = parsed.get("_source", {})
    raw_text_storage = raw_text[:50000] if raw_text else ""

    return resume_create, source_meta, {"raw_text": raw_text_storage, "source": source_meta}


def parse_resume_full(
    raw_text: str,
    resume_name: str = "Imported Resume",
    use_ai: bool = True,
) -> Dict[str, Any]:
    """Run the full resume parsing pipeline.

    Args:
        raw_text: Raw text extracted from a PDF resume.
        resume_name: Name for the resume record.
        use_ai: Whether to attempt AI enrichment. Default True.

    Returns:
        Dict with keys:
          - resume_create: ResumeCreate schema ready for DB
          - source_meta: Source provenance metadata
          - enriched_data: Raw enriched data dict
          - raw_text: Original raw text (truncated to 50k)
          - ai_used: Whether AI was attempted
          - sections: Section-detected raw text
          - deterministic: Deterministic parsing result
    """
    # Step 1: Section detection (Phase 2B)
    sections = detect_sections(raw_text)

    # Step 2: Deterministic parsing (Phase 2C)
    deterministic = parse_resume(raw_text)

    # Step 3: AI enrichment (Phase 2D)
    if use_ai:
        enriched, source_meta = enrich_deterministic_with_ai(deterministic, sections)
        ai_used = True
    else:
        enriched = dict(deterministic)
        source_meta = {s: {"ai_success": False, "sources": {"_all": "rule"}}
                       for s in deterministic}
        ai_used = False

    # Step 4: Build ResumeCreate with Pydantic validation
    resume_create, pipeline_source_meta, enriched_data = _build_resume_create(
        enriched, resume_name, raw_text
    )

    return {
        "resume_create": resume_create,
        "parsed_data": enriched,
        "source_meta": pipeline_source_meta,
        "enriched_data": enriched_data,
        "raw_text": raw_text[:50000] if raw_text else "",
        "ai_used": ai_used,
        "sections": sections,
        "deterministic": deterministic,
    }
