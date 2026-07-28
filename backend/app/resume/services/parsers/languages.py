"""Deterministic languages section parser."""
import re
from typing import Any, Dict, List


# Patterns for language: proficiency separators
_PROFICIENCY_SEPARATORS = re.compile(
    r"\s*[–\-—|:;•/()]\s*"
)

# Proficiency indicators
_PROFICIENCY_LEVELS = [
    "native", "fluent", "advanced", "intermediate",
    "conversational", "basic", "elementary",
    "c2", "c1", "b2", "b1", "a2", "a1",
    "professional working",
    "full professional",
    "limited working",
]


def _split_language_line(line: str) -> List[Dict[str, str]]:
    """Split a line into (language, proficiency) pairs."""
    results: List[Dict[str, str]] = []

    # Try comma-separated items first
    items = [item.strip() for item in re.split(r",\s*", line) if item.strip()]

    for item in items:
        # Try to split by proficiency separators
        parts = _PROFICIENCY_SEPARATORS.split(item, maxsplit=1)
        if len(parts) == 2:
            lang = parts[0].strip()
            prof = parts[1].strip().lower()
            # Validate it's actually a proficiency level
            if any(level in prof for level in _PROFICIENCY_LEVELS):
                results.append({"language": lang, "proficiency": prof.title()})
                continue
            # Could be e.g., "English (US)" — keep as language only
            results.append({"language": item.strip(), "proficiency": ""})
        else:
            # Check if parenthetical contains proficiency
            paren_match = re.search(r"\((.+?)\)", item)
            if paren_match:
                potential_prof = paren_match.group(1).strip().lower()
                if any(level in potential_prof for level in _PROFICIENCY_LEVELS):
                    lang = item[:paren_match.start()].strip()
                    results.append({
                        "language": lang,
                        "proficiency": potential_prof.title(),
                    })
                    continue
            results.append({"language": item.strip(), "proficiency": ""})

    return results


def parse_languages(raw_text: str) -> List[Dict[str, Any]]:
    """Parse languages section into a list of structured entries.

    Args:
        raw_text: Raw text from the languages section.

    Returns:
        List of dicts with keys: language, proficiency.
    """
    if not raw_text or not raw_text.strip():
        return []

    results: List[Dict[str, Any]] = []

    for line in raw_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        results.extend(_split_language_line(stripped))

    # Deduplicate by language name (case-insensitive)
    seen: set = set()
    deduped: List[Dict[str, Any]] = []
    for entry in results:
        key = entry["language"].strip().lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(entry)

    return deduped
