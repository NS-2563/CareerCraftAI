"""AI-assisted resume parser — enrichment/fallback on top of deterministic parsing.

Phase 2D of Intelligent Resume Import.

Architecture:
  Deterministic Parsing → AI Enrichment → Merge → Normalize → Validate

AI never replaces the deterministic result for high-confidence fields.
It fills gaps, improves descriptions, and catches what rules miss.

Graceful fallback: if Gemini is unavailable, times out, or returns
invalid data, the deterministic result is used as-is.
"""
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.ai.json_parser import extract_json, JSONParseError
from app.ai.response_repair import repair_json, try_repair_json
from app.resume.services.resume_prompt import (
    get_section_prompt,
    get_section_names,
    is_supported_section,
)
from app.schemas.resume import (
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
from app.utils.sanitizer import sanitize_ai_output

logger = logging.getLogger(__name__)

# Maximum characters per section before we skip AI parsing for that section.
# Gemini 2.0 Flash has large context, but we keep sections manageable.
_MAX_SECTION_CHARS = 8000

# Threshold: deterministic description shorter than this → prefer AI description
_DESCRIPTION_QUALITY_THRESHOLD = 20

# Sections that contain list-type data (arrays of objects)
_LIST_SECTIONS = {
    "experience": ExperienceItem,
    "education": EducationItem,
    "skills": SkillItem,
    "projects": ProjectItem,
    "certifications": CertificationItem,
    "languages": LanguageItem,
    "interests": InterestItem,
    "references": ReferenceItem,
}

# High-confidence deterministic fields — AI should NOT override these
# when the deterministic parser found a non-empty value.
_HIGH_CONFIDENCE_FIELDS = {
    "personal": {"firstName", "lastName", "email", "phone", "linkedin", "github", "portfolio"},
    "experience": {"company", "position", "startDate", "endDate", "current"},
    "education": {"institution", "degree", "startDate", "endDate", "current"},
    "skills": {"name"},
    "projects": {"name"},
    "certifications": {"name", "issuer"},
    "languages": {"language"},
    "interests": {"name"},
    "references": {"name"},
}


class AIParseResult:
    """Result of AI parsing for a single section or the full resume.

    Attributes:
        data: The parsed/enriched data dict for this section.
        source: Dict mapping field paths to source ("rule", "ai", "merged").
        success: Whether AI parsing succeeded for this section.
        error: Error message if AI parsing failed.
    """

    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.source: Dict[str, str] = {}
        self.success: bool = False
        self.error: Optional[str] = None


def _call_ai(prompt: str) -> Optional[str]:
    """Call the configured AI provider with the given prompt.

    Returns the response text, or None if the call fails.
    Never raises — all errors are caught and logged.
    """
    try:
        from app.providers.factory import get_provider
        provider = get_provider()
        response = provider._generate_content(prompt)
        if response and response.strip():
            return response.strip()
        logger.warning("AI returned empty response")
        return None
    except Exception as e:
        logger.warning("AI call failed: %s", str(e))
        return None


def _parse_ai_json_response(response: str) -> Optional[Any]:
    """Parse JSON from the AI response, handling markdown and minor repairs.

    Returns parsed JSON or None on failure.
    """
    if not response:
        return None

    try:
        # First try: extract JSON from potentially markdown-wrapped response
        return extract_json(response)
    except JSONParseError:
        pass

    try:
        # Second try: repair common issues then parse
        return try_repair_json(response)
    except JSONParseError:
        pass

    # Third try: manual repair + extract
    try:
        repaired = repair_json(response)
        return extract_json(repaired)
    except JSONParseError:
        logger.debug("All JSON parsing attempts failed")
        return None


_CAMEL_TO_SNAKE_MAP = {
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

_SNAKE_TO_CAMEL_MAP = {v: k for k, v in _CAMEL_TO_SNAKE_MAP.items()}


def _camel_to_snake(data: Any) -> Any:
    """Convert camelCase keys to snake_case."""
    if isinstance(data, dict):
        return {_CAMEL_TO_SNAKE_MAP.get(k, k): _camel_to_snake(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_camel_to_snake(item) for item in data]
    return data


def _snake_to_camel(data: Any) -> Any:
    """Convert snake_case keys to camelCase."""
    if isinstance(data, dict):
        return {_SNAKE_TO_CAMEL_MAP.get(k, k): _snake_to_camel(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_snake_to_camel(item) for item in data]
    return data


_PERSONAL_REQUIRED_FIELDS = {"first_name", "last_name", "email", "phone", "location"}


def _validate_section_data(section_name: str, data: Any) -> Any:
    """Validate section data against the appropriate Pydantic schema.

    For list sections, validates each item.
    For scalar sections (personal, summary), validates as a single dict.

    Returns validated data in camelCase format, or None if validation fails.
    """
    if data is None:
        return None

    if isinstance(data, list) and len(data) == 0:
        return []

    if section_name == "personal":
        if isinstance(data, dict):
            try:
                snake_data = _camel_to_snake(data)
                validated = PersonalInfo(**snake_data)
                dumped = validated.model_dump(exclude_none=True)
                # Require at least one meaningful field
                if not any(dumped.get(f) for f in _PERSONAL_REQUIRED_FIELDS):
                    logger.debug("Personal info has no meaningful fields")
                    return None
                return _snake_to_camel(dumped)
            except Exception as e:
                logger.debug("Personal info validation failed: %s", str(e))
                return None
        return None

    if section_name == "summary":
        if isinstance(data, dict) and "summary" in data:
            text = sanitize_ai_output(data.get("summary", "")) or ""
            return {"summary": text}
        return None

    model_class = _LIST_SECTIONS.get(section_name)
    if model_class is None:
        return None

    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return None

    validated_items = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            snake_item = _camel_to_snake(item)
            validated = model_class(**snake_item)
            validated_items.append(_snake_to_camel(validated.model_dump(exclude_none=True)))
        except Exception as e:
            logger.debug("Item validation failed for %s: %s", section_name, str(e))
            continue

    return validated_items if validated_items else None


def _match_ai_to_deterministic(
    ai_entries: List[Dict], det_entries: List[Dict], match_fields: List[str]
) -> List[Tuple[Optional[Dict], Optional[Dict]]]:
    """Match AI entries to deterministic entries by key fields.

    Returns list of (deterministic_entry, ai_entry) pairs.
    Unmatched entries appear as (det_entry, None) or (None, ai_entry).
    """
    matched: List[Tuple[Optional[Dict], Optional[Dict]]] = []
    used_ai: set = set()

    # Use deterministic order as primary, match AI entries to them
    for det in det_entries:
        best_match = None
        best_idx = -1
        for i, ai in enumerate(ai_entries):
            if i in used_ai:
                continue
            score = _compute_match_score(det, ai, match_fields)
            if score > 0 and (best_match is None or score > _compute_match_score(det, best_match, match_fields)):
                best_match = ai
                best_idx = i

        if best_match is not None:
            used_ai.add(best_idx)
            matched.append((det, best_match))
        else:
            matched.append((det, None))

    # Remaining AI entries (no deterministic match)
    for i, ai in enumerate(ai_entries):
        if i not in used_ai:
            matched.append((None, ai))

    return matched


def _compute_match_score(det: Dict, ai: Dict, fields: List[str]) -> int:
    """Compute a simple match score between two entries."""
    score = 0
    for field in fields:
        d_val = str(det.get(field, "")).strip().lower()
        a_val = str(ai.get(field, "")).strip().lower()
        if d_val and a_val and (d_val == a_val or d_val in a_val or a_val in d_val):
            score += 1
    return score


def _merge_section(
    section_name: str,
    deterministic: Any,
    ai_data: Any,
) -> Tuple[Any, Dict[str, str]]:
    """Merge deterministic and AI results for a single section.

    Returns (merged_data, source_map) where source_map tracks provenance.
    """
    source: Dict[str, str] = {}

    if section_name == "personal":
        return _merge_personal(deterministic, ai_data, source)
    if section_name == "summary":
        return _merge_summary(deterministic, ai_data, source)
    if section_name in _LIST_SECTIONS:
        return _merge_list_section(section_name, deterministic, ai_data, source)

    return deterministic, {"_default": "rule"}


def _merge_personal(
    det: Dict[str, Any], ai: Optional[Dict[str, Any]], source: Dict[str, str]
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Merge personal info — deterministic fields take precedence."""
    result = dict(det) if det else {}
    high_conf = _HIGH_CONFIDENCE_FIELDS.get("personal", set())

    for key in list(result.keys()):
        source[key] = "rule"

    if ai and isinstance(ai, dict):
        for key, value in ai.items():
            if value is not None and value != "":
                if key in high_conf:
                    # Deterministic wins if non-empty
                    if not result.get(key):
                        result[key] = value
                        source[key] = "ai"
                else:
                    # AI fills non-high-confidence fields
                    if not result.get(key):
                        result[key] = value
                        source[key] = "ai"

    return result, source


def _merge_summary(
    det: str, ai: Optional[Dict[str, Any]], source: Dict[str, str]
) -> Tuple[str, Dict[str, str]]:
    """Merge summary — prefer AI result if available and meaningful."""
    ai_summary = ""
    if ai and isinstance(ai, dict):
        ai_summary = (ai.get("summary") or "").strip()

    if ai_summary and len(ai_summary) > len(det):
        source["summary"] = "ai"
        return ai_summary, source

    source["summary"] = "rule"
    return det, source


def _merge_list_section(
    section_name: str,
    det_list: List[Dict],
    ai_list: Optional[List[Dict]],
    source: Dict[str, str],
) -> Tuple[List[Dict], Dict[str, str]]:
    """Merge a list-type section by matching entries."""
    det_list = det_list or []
    ai_list = ai_list or []

    high_conf = _HIGH_CONFIDENCE_FIELDS.get(section_name, set())

    if section_name == "experience":
        match_keys = ["company", "position"]
    elif section_name == "education":
        match_keys = ["institution", "degree"]
    elif section_name == "projects":
        match_keys = ["name"]
        # Normalize deterministic entries: title → name for matching
        det_list = [dict(d) for d in det_list]
        for det in det_list:
            if "title" in det and "name" not in det:
                det["name"] = det["title"]
    elif section_name == "certifications":
        match_keys = ["name"]
    elif section_name in ("skills", "languages", "interests"):
        match_keys = ["name"]
    elif section_name == "references":
        match_keys = ["name"]
    else:
        match_keys = ["name"]

    if not ai_list:
        for item in det_list:
            for key in item:
                source[f"{key}"] = "rule"
        merged = list(det_list)
    elif not det_list:
        for i, item in enumerate(ai_list):
            for key in item:
                source[f"ai_entry_{i}_{key}"] = "ai"
        merged = list(ai_list)
    else:
        pairs = _match_ai_to_deterministic(ai_list, det_list, match_keys)

        merged = []
        for idx, (det_entry, ai_entry) in enumerate(pairs):
            if det_entry and ai_entry:
                merged_item = dict(det_entry)
                for key in ai_entry:
                    ai_val = ai_entry.get(key)
                    if ai_val is not None and ai_val != "" and ai_val != []:
                        if key in high_conf:
                            if not merged_item.get(key):
                                merged_item[key] = ai_val
                                source[f"entry_{idx}_{key}"] = "ai"
                            else:
                                source[f"entry_{idx}_{key}"] = "rule"
                        else:
                            existing = merged_item.get(key)
                            if not existing or (
                                isinstance(existing, str) and len(existing) < _DESCRIPTION_QUALITY_THRESHOLD
                                and key in ("description",)
                            ):
                                merged_item[key] = ai_val
                                source[f"entry_{idx}_{key}"] = "ai"
                            else:
                                source[f"entry_{idx}_{key}"] = "rule"
                merged.append(merged_item)
            elif det_entry and not ai_entry:
                for key in det_entry:
                    source[f"entry_{idx}_{key}"] = "rule"
                merged.append(det_entry)
            elif ai_entry and not det_entry:
                item = {}
                for key, value in ai_entry.items():
                    if value is not None and value != "" and value != []:
                        item[key] = value
                        source[f"entry_{idx}_{key}"] = "ai"
                if item:
                    merged.append(item)

    # Normalize project field names: frontend expects title, not name
    if section_name == "projects":
        for item in merged:
            if "name" in item and "title" not in item:
                item["title"] = item.pop("name")

    return merged, source


def _chunk_section_text(text: str, max_chars: int = _MAX_SECTION_CHARS) -> List[str]:
    """Split long section text into chunks for AI processing.

    Splits at entry boundaries (double newlines) when possible.
    """
    if not text or len(text) <= max_chars:
        return [text] if text else []

    entries = [e.strip() for e in text.split("\n\n") if e.strip()]
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for entry in entries:
        entry_len = len(entry)
        if current_len + entry_len > max_chars and current:
            chunks.append("\n\n".join(current))
            current = [entry]
            current_len = entry_len
        else:
            current.append(entry)
            current_len += entry_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def parse_section_with_ai(
    section_name: str,
    section_text: str,
    deterministic_context: Optional[Dict[str, Any]] = None,
) -> AIParseResult:
    """Parse a single resume section using AI.

    Args:
        section_name: Section key (personal, experience, etc.).
        section_text: Raw section text from section detector.
        deterministic_context: Deterministic parsing result for context hints.

    Returns:
        AIParseResult with parsed data, source metadata, and success status.
    """
    result = AIParseResult()

    if not is_supported_section(section_name):
        result.error = f"Unsupported section: {section_name}"
        return result

    if not section_text or not section_text.strip():
        result.success = True
        result.data = deterministic_context or {}
        return result

    if len(section_text) > _MAX_SECTION_CHARS:
        logger.info("Section '%s' exceeds %d chars (%d), skipping AI parsing",
                     section_name, _MAX_SECTION_CHARS, len(section_text))
        result.data = deterministic_context or {}
        result.source["_skipped"] = "too_long"
        return result

    context_for_prompt = None
    if deterministic_context is not None:
        ctx: Dict[str, Any] = {}
        if isinstance(deterministic_context, dict) and section_name != "summary":
            for key, value in deterministic_context.items():
                if value is not None and value != "" and value != []:
                    ctx[key] = value
        elif isinstance(deterministic_context, list):
            for item in deterministic_context[:3]:
                if isinstance(item, dict):
                    for key, value in item.items():
                        if value and key not in ctx:
                            ctx[key] = value
        context_for_prompt = ctx if ctx else None

    prompt = get_section_prompt(section_name, section_text, context_for_prompt)
    if not prompt:
        result.error = "No prompt available"
        return result

    try:
        response = _call_ai(prompt)
    except Exception as e:
        logger.warning("AI call raised exception for section '%s': %s", section_name, str(e))
        response = None

    if response is None:
        result.error = "AI call failed"
        logger.info("AI parse failed for section '%s', falling back to deterministic", section_name)
        result.data = deterministic_context or {}
        return result

    parsed = _parse_ai_json_response(response)
    if parsed is None:
        result.error = "Failed to parse AI response as JSON"
        logger.info("AI JSON parse failed for section '%s', falling back to deterministic", section_name)
        result.data = deterministic_context or {}
        return result

    validated = _validate_section_data(section_name, parsed)
    if validated is None:
        result.error = "AI response failed schema validation"
        logger.info("AI schema validation failed for section '%s', falling back to deterministic", section_name)
        result.data = deterministic_context or {}
        return result

    result.success = True
    if section_name == "summary":
        result.data = validated
    else:
        result.data = validated

    return result


def enrich_deterministic_with_ai(
    deterministic_result: Dict[str, Any],
    sections: Dict[str, str],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Enrich deterministic parsing result with AI.

    For each section, attempts AI parsing. On success, merges AI data
    with deterministic data. On failure, uses deterministic as-is.

    Args:
        deterministic_result: Output from structured_parser.parse_resume().
        sections: Raw section text from section_detector.detect_sections().

    Returns:
        Tuple of (merged_result, source_metadata).
        source_metadata maps each section to its source info.
    """
    merged = {}
    source_meta: Dict[str, Any] = {}

    # Section text mapping: section_detector uses "header" for personal info
    _SECTION_TEXT_KEYS = {"personal": "header"}
    for section_name in get_section_names():
        det_data = deterministic_result.get(section_name)
        text_key = _SECTION_TEXT_KEYS.get(section_name, section_name)
        section_text = sections.get(text_key, "")

        # Skip AI parsing for empty sections
        if not section_text or not section_text.strip():
            merged[section_name] = det_data if det_data is not None else (
                [] if section_name in _LIST_SECTIONS else ""
            )
            source_meta[section_name] = {
                "ai_success": False,
                "skipped": "empty",
                "sources": {"_all": "rule"},
            }
            continue

        ai_result = parse_section_with_ai(section_name, section_text, det_data)

        if ai_result.success and ai_result.data is not None:
            merged_section, section_source = _merge_section(
                section_name, det_data, ai_result.data
            )
            merged[section_name] = merged_section
            source_meta[section_name] = {
                "ai_success": True,
                "sources": section_source,
            }
        else:
            merged[section_name] = det_data if det_data is not None else (
                [] if section_name in _LIST_SECTIONS else ""
            )
            source_meta[section_name] = {
                "ai_success": False,
                "error": ai_result.error,
                "sources": {"_all": "rule"},
            }

    # Copy over any non-section keys from deterministic result
    for key in deterministic_result:
        if key not in merged:
            merged[key] = deterministic_result[key]

    return merged, source_meta
