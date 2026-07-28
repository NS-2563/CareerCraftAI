"""Resume section detector — deterministic rule-based section boundary detection.

Phase 2B of Intelligent Resume Import.
Zero AI dependency. Zero database changes. Zero frontend changes.
"""
import re
from typing import Dict, List, Tuple


# Section heading patterns.
# Ordered by specificity within each group (more specific first).
# Each entry: (section_id, compiled_regex)
# The regex captures three groups:
#   1 — the heading text itself
#   2 — an optional colon
#   3 — any content after the colon
#
# A line is accepted as a real heading only when:
#   - it has an explicit colon after the heading text, OR
#   - there is no content after the heading text (standalone heading)
# This prevents false positives when a heading keyword appears
# mid-sentence ("Experience is the best teacher" -> rejected).

_HEADING_DEFINITIONS: List[Tuple[str, List[str]]] = [
    ("summary", [
        r"professional\s+summary",
        r"summary\s+of\s+qualifications",
        r"summary\s+of\s+skills",
        r"career\s+objective",
        r"personal\s+statement",
        r"profile",
        r"objective",
        r"about\s+me",
        r"summary",
    ]),
    ("experience", [
        r"professional\s+experience",
        r"work\s+experience",
        r"employment\s+history",
        r"career\s+history",
        r"work\s+history",
        r"professional\s+background",
        r"professional\s+history",
        r"relevant\s+experience",
        r"experience",
    ]),
    ("education", [
        r"education\s+and\s+qualifications",
        r"academic\s+background",
        r"academic\s+history",
        r"academic\s+qualifications",
        r"education",
        r"qualifications",
    ]),
    ("skills", [
        r"technical\s+skills",
        r"core\s+competencies",
        r"areas?\s+of\s+expertise",
        r"tools\s+and\s+technologies",
        r"skills\s+and\s+abilities",
        r"skills\s+and\s+expertise",
        r"technologies",
        r"competencies",
        r"tools",
        r"skills",
    ]),
    ("projects", [
        r"personal\s+projects",
        r"side\s+projects",
        r"key\s+projects",
        r"notable\s+projects",
        r"project\s+experience",
        r"projects",
    ]),
    ("certifications", [
        r"professional\s+certifications",
        r"licenses?\s+and\s+certifications",
        r"certifications\s+and\s+licenses?",
        r"certifications",
        r"licenses?",
    ]),
    ("languages", [
        r"linguistic\s+abilities",
        r"language\s+proficiency",
        r"languages",
    ]),
    ("interests", [
        r"personal\s+interests",
        r"interests",
        r"hobbies",
        r"activities",
    ]),
    ("references", [
        r"professional\s+references",
        r"references",
    ]),
    ("achievements", [
        r"key\s+achievements",
        r"notable\s+achievements",
        r"honors?\s+and\s+awards",
        r"achievements",
        r"accomplishments",
        r"awards",
        r"honors?",
    ]),
]

# Personal/contact information heading — maps to the header section.
# This is handled separately because the header section is special
# (it contains text before the first recognised section heading).
_HEADER_PATTERNS = [
    r"personal\s+information",
    r"contact\s+information",
    r"contact\s+details",
    r"personal\s+details",
]
_HEADER_REGEX = re.compile(
    r"^\s*(" + "|".join(_HEADER_PATTERNS) + r")\s*(:)?\s*(.*)$",
    re.IGNORECASE,
)

# Compile all section heading regexes.
_SECTION_REGEXES: List[Tuple[str, re.Pattern]] = []
for section_id, patterns in _HEADING_DEFINITIONS:
    for pattern in patterns:
        regex = re.compile(
            r"^\s*(" + pattern + r")\s*(:)?\s*(.*)$",
            re.IGNORECASE,
        )
        _SECTION_REGEXES.append((section_id, regex))

# All recognised section keys.
_SECTION_KEYS = [
    "header",
    "summary",
    "experience",
    "education",
    "skills",
    "projects",
    "certifications",
    "languages",
    "interests",
    "references",
    "achievements",
    "unknown",
]

# Maximum length (trimmed) for a line to be considered a potential heading.
_MAX_HEADING_LINE_LENGTH = 120


def _make_empty_result() -> Dict[str, str]:
    """Return a result dict with all section keys initialised to empty strings."""
    return {key: "" for key in _SECTION_KEYS}


def _try_match_heading(
    stripped: str,
) -> Tuple[bool, str, str]:
    """Try to match a line against all section heading patterns.

    Args:
        stripped: A trimmed text line.

    Returns:
        Tuple of (matched, section_id, after_colon_content).
        If not matched, section_id and after_colon_content are empty strings.
    """
    # Reject lines that are too long to be headings.
    if len(stripped) > _MAX_HEADING_LINE_LENGTH:
        return False, "", ""

    for section_id, regex in _SECTION_REGEXES:
        m = regex.match(stripped)
        if m:
            heading_text = m.group(1).strip()
            has_colon = m.group(2) is not None and m.group(2) == ":"
            after_colon = m.group(3).strip() if m.group(3) else ""

            # A real heading must have an explicit colon OR no trailing content.
            if has_colon or not after_colon:
                return True, section_id, after_colon

            # Heading keyword with non-colon continuation is a false positive
            # (e.g. "Experience is the best teacher").
            continue

    return False, "", ""


def _try_match_header(stripped: str) -> Tuple[bool, str]:
    """Try to match a line against the personal/contact header patterns.

    Args:
        stripped: A trimmed text line.

    Returns:
        Tuple of (matched, after_colon_content).
    """
    if len(stripped) > _MAX_HEADING_LINE_LENGTH:
        return False, ""

    m = _HEADER_REGEX.match(stripped)
    if m:
        heading_text = m.group(1).strip()
        has_colon = m.group(2) is not None and m.group(2) == ":"
        after_colon = m.group(3).strip() if m.group(3) else ""
        if has_colon or not after_colon:
            return True, after_colon

    return False, ""


def detect_sections(raw_text: str) -> Dict[str, str]:
    """Detect resume section boundaries in raw PDF text.

    Processes text line-by-line, identifying section headings using
    deterministic pattern matching. Only lines that look like genuine
    standalone headings (short, colon-delimited or bare) trigger a
    section transition.

    Args:
        raw_text: Raw text extracted from a PDF resume.

    Returns:
        Dict with keys: header, summary, experience, education, skills,
        projects, certifications, languages, interests, references,
        achievements, unknown.
        Missing sections have empty string values.

    Raises:
        TypeError: If raw_text is not a string.
    """
    if not isinstance(raw_text, str):
        raise TypeError(f"Expected str, got {type(raw_text).__name__}")

    result = _make_empty_result()

    if not raw_text or not raw_text.strip():
        return result

    lines = raw_text.split("\n")
    current_section = "header"
    heading_was_detected = False

    for line in lines:
        stripped = line.strip()

        # Preserve blank lines as structural separators within content.
        if not stripped:
            result[current_section] += "\n"
            continue

        # Check for personal/contact heading -> switch to header section.
        header_matched, after_colon = _try_match_header(stripped)
        if header_matched:
            heading_was_detected = True
            current_section = "header"
            if after_colon:
                result[current_section] += after_colon + "\n"
            continue

        # Check for all other section headings.
        matched, section_id, after_colon = _try_match_heading(stripped)
        if matched:
            heading_was_detected = True
            current_section = section_id
            if after_colon:
                result[current_section] += after_colon + "\n"
            continue

        # Regular content line — append to current section.
        result[current_section] += stripped + "\n"

    # If no headings were detected at all, the unstructured content
    # goes into the "unknown" bucket.
    if not heading_was_detected and result["header"].strip():
        result["unknown"] = result["header"].strip()
        result["header"] = ""

    # Strip trailing whitespace from every section.
    for key in result:
        result[key] = result[key].strip()

    return result
