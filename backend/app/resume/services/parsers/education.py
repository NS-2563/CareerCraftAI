"""Deterministic education section parser."""
import re
from typing import Any, Dict, List

from app.resume.services.parser_utils import (
    parse_date_range,
    split_entries,
)


# Common education entry first-line patterns.
_ENTRY_LINE_PATTERNS = [
    # "Degree in Field, Institution, Location | Date - Date"
    re.compile(
        r"^\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*$"
    ),
    # "Degree in Field, Institution | Date - Date"
    re.compile(
        r"^\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*$"
    ),
    # "Degree in Field, Institution (Date - Date)"
    re.compile(
        r"^\s*(.+?),\s*(.+?)\s*\((.+?)\)\s*$"
    ),
    # "Degree at Institution (Date - Date)"
    re.compile(
        r"^\s*(.+?)\s+at\s+(.+?)\s*\((.+?)\)\s*$", re.IGNORECASE
    ),
    # "Institution — Degree, Field of Study | Date - Date"
    re.compile(
        r"^\s*(.+?)\s*[–\-—]\s*(.+?),\s*(.+?)\s*\|\s*(.+?)\s*$"
    ),
]

# GPA patterns
_GPA_RE = re.compile(r"\b(\d\.\d)\s*/?\s*4\.?0?\b", re.IGNORECASE)


def _parse_entry_line(line: str) -> Dict[str, str]:
    """Parse the first line of an education entry."""
    result = {
        "institution": "",
        "degree": "",
        "field_of_study": "",
        "location": "",
        "start_date": "",
        "end_date": "",
        "current": False,
    }

    if not line:
        return result

    _LOCATION_RE = re.compile(r"^[A-Za-z\s]+,\s*[A-Z]{2}\b")

    for idx, pattern in enumerate(_ENTRY_LINE_PATTERNS):
        m = pattern.match(line)
        if m:
            groups = m.groups()
            if len(groups) == 4:
                result["institution"] = groups[0].strip()
                result["degree"] = groups[1].strip()
                third = groups[2].strip()
                fourth = groups[3].strip()

                dr_start, dr_end, dr_current = parse_date_range(fourth)
                if dr_start or dr_end:
                    result["start_date"] = dr_start
                    result["end_date"] = dr_end
                    result["current"] = dr_current
                    # Heuristic: if third looks like a location, set location
                    if _LOCATION_RE.match(third):
                        result["location"] = third
                    else:
                        result["field_of_study"] = third
                else:
                    result["location"] = third
                    dr_start2, dr_end2, dr_current2 = parse_date_range(fourth)
                    result["start_date"] = dr_start2
                    result["end_date"] = dr_end2
                    result["current"] = dr_current2
                return result

            elif len(groups) == 3:
                first = groups[0].strip()
                second = groups[1].strip()
                third = groups[2].strip()

                dr_start, dr_end, dr_current = parse_date_range(third)
                if dr_start or dr_end:
                    # Pipe format (idx 0, 1): first=institution, second=degree
                    if idx <= 1:
                        result["institution"] = first
                        result["degree"] = second
                    else:
                        result["degree"] = first
                        result["institution"] = second
                    result["start_date"] = dr_start
                    result["end_date"] = dr_end
                    result["current"] = dr_current
                    return result

                result["institution"] = first
                result["degree"] = second
                result["field_of_study"] = third
                return result

    return result


def _extract_gpa(text: str) -> str:
    """Extract GPA from text."""
    m = _GPA_RE.search(text)
    return m.group(1) if m else ""


def _parse_single_entry(text: str) -> Dict[str, Any]:
    """Parse a single education entry block.

    Returns dict with camelCase keys: institution, degree, fieldOfStudy,
    location, startDate, endDate, current, gpa, description.
    """
    result: Dict[str, Any] = {
        "institution": "",
        "degree": "",
        "fieldOfStudy": "",
        "location": "",
        "startDate": "",
        "endDate": "",
        "current": False,
        "gpa": "",
        "description": "",
    }

    if not text or not text.strip():
        return result

    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if not lines:
        return result

    first_line = lines[0]
    parsed = _parse_entry_line(first_line)

    result["institution"] = parsed.get("institution", "")
    result["degree"] = parsed.get("degree", "")
    result["fieldOfStudy"] = parsed.get("field_of_study", "")
    result["location"] = parsed.get("location", "")
    result["startDate"] = parsed.get("start_date", "")
    result["endDate"] = parsed.get("end_date", "")
    result["current"] = parsed.get("current", False)

    # Search all lines for GPA
    for line in lines:
        gpa = _extract_gpa(line)
        if gpa:
            result["gpa"] = gpa
            break

    # Remaining lines → description
    if len(lines) > 1:
        desc_lines = [l for l in lines[1:] if l.lower() != first_line.lower()]
        desc_lines = [l for l in desc_lines if _GPA_RE.search(l) is None]
        result["description"] = " ".join(desc_lines)

    return result


def _looks_like_entry_line(line: str) -> bool:
    """Check if a line looks like an education entry first line."""
    for pattern in _ENTRY_LINE_PATTERNS:
        if pattern.match(line):
            return True
    return False


def _split_education_lines(raw_text: str) -> List[str]:
    """Split education text into entries by entry-pattern lines.

    Education entries are often separated by single newlines (no blank line).
    Each line matching an entry pattern starts a new entry; subsequent
    non-matching lines are appended as description.
    """
    if not raw_text or not raw_text.strip():
        return []

    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
    if not lines:
        return []

    entries: List[List[str]] = []
    for line in lines:
        if _looks_like_entry_line(line) or not entries:
            entries.append([line])
        else:
            entries[-1].append(line)

    return ["\n".join(e) for e in entries]


def parse_education(raw_text: str) -> List[Dict[str, Any]]:
    """Parse education section into a list of structured entries.

    Args:
        raw_text: Raw text from the education section.

    Returns:
        List of dicts with camelCase keys: institution, degree,
        fieldOfStudy, location, startDate, endDate, current, gpa,
        description.
    """
    if not raw_text or not raw_text.strip():
        return []

    raw_entries = _split_education_lines(raw_text)
    results = [_parse_single_entry(e) for e in raw_entries if e.strip()]

    results = [
        r for r in results
        if r.get("institution") or r.get("degree")
    ]

    return results
