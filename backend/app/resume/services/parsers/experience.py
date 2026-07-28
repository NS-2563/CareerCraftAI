"""Deterministic experience section parser."""
import re
from typing import Any, Dict, List, Tuple

from app.resume.services.parser_utils import (
    parse_date_range,
    split_entries,
)


# Common experience entry first-line patterns.
# Each pattern captures groups: (company, position, location, date_range)
_ENTRY_LINE_PATTERNS = [
    # "Company | Position | Location | Date - Date"
    re.compile(
        r"^\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*$"
    ),
    # "Company | Position | Date - Date"
    re.compile(
        r"^\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*$"
    ),
    # "Position at Company (Date - Date)"
    re.compile(
        r"^\s*(.+?)\s+at\s+(.+?)\s*\((.+?)\)\s*$", re.IGNORECASE
    ),
    # "Position at Company | Location | Date - Date"
    re.compile(
        r"^\s*(.+?)\s+at\s+(.+?)\s*\|\s*(.+?)\s*$", re.IGNORECASE
    ),
    # "Company - Position (Date - Date)"
    re.compile(
        r"^\s*(.+?)\s*[–\-—]\s*(.+?)\s*\((.+?)\)\s*$"
    ),
    # "Company — Position, Location | Date - Date" (em dash)
    re.compile(
        r"^\s*(.+?)\s*—\s*(.+?),\s*(.+?)\s*\|\s*(.+?)\s*$"
    ),
    # "Company | Position" (no date)
    re.compile(
        r"^\s*(.+?)\s*\|\s*(.+?)\s*$"
    ),
]

# Fallback: try to extract a date range from anywhere on the first line.
_DATE_RANGE_INLINE = re.compile(
    r"\(?(\d{4}|\w+\s+\d{4}|\d{1,2}/\d{4})\s*[–\-—to]+\s*(.+?)\)?"
)


def _parse_entry_line(line: str) -> Dict[str, str]:
    """Parse the first line of an experience entry.

    Returns dict with keys: company, position, location, start_date,
    end_date, current.
    """
    result = {
        "company": "",
        "position": "",
        "location": "",
        "start_date": "",
        "end_date": "",
        "current": False,
    }

    if not line:
        return result

    for idx, pattern in enumerate(_ENTRY_LINE_PATTERNS):
        m = pattern.match(line)
        if m:
            groups = m.groups()
            if len(groups) == 4:
                # company | position | location | date_range
                result["company"] = groups[0].strip()
                result["position"] = groups[1].strip()
                result["location"] = groups[2].strip()
                date_range = groups[3].strip()
                start, end, current = parse_date_range(date_range)
                result["start_date"] = start
                result["end_date"] = end
                result["current"] = current
                return result
            elif len(groups) == 3:
                first = groups[0].strip()
                second = groups[1].strip()
                third = groups[2].strip()

                # Check if third looks like a date range
                dr_start, dr_end, dr_current = parse_date_range(third)
                if dr_start or dr_end:
                    # Index 2 = "Position at Company (Date)" → groups: position, company, date
                    if idx == 2:
                        result["company"] = second
                        result["position"] = first
                    else:
                        result["company"] = first
                        result["position"] = second
                    result["start_date"] = dr_start
                    result["end_date"] = dr_end
                    result["current"] = dr_current
                    return result

                # Could be "company | position | location"
                result["company"] = first
                result["position"] = second
                result["location"] = third
                return result

            elif len(groups) == 2:
                # "Company | Position" (no date)
                result["company"] = groups[0].strip()
                result["position"] = groups[1].strip()
                return result

    # Fallback: try to extract date range from anywhere in the line
    drm = _DATE_RANGE_INLINE.search(line)
    if drm:
        range_text = f"{drm.group(1)} - {drm.group(2)}"
        start, end, current = parse_date_range(range_text)
        result["start_date"] = start
        result["end_date"] = end
        result["current"] = current

    return result


def _parse_single_entry(text: str) -> Dict[str, Any]:
    """Parse a single experience entry block.

    Args:
        text: Raw text for one experience entry.

    Returns:
        Dict with camelCase keys: company, position, location,
        startDate, endDate, current, description.
    """
    result: Dict[str, Any] = {
        "company": "",
        "position": "",
        "location": "",
        "startDate": "",
        "endDate": "",
        "current": False,
        "description": "",
    }

    if not text or not text.strip():
        return result

    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if not lines:
        return result

    # Parse first line for structured fields
    first_line = lines[0]
    parsed = _parse_entry_line(first_line)

    # Map snake_case parsed fields to camelCase
    result["company"] = parsed.get("company", "")
    result["position"] = parsed.get("position", "")
    result["location"] = parsed.get("location", "")
    result["startDate"] = parsed.get("start_date", "")
    result["endDate"] = parsed.get("end_date", "")
    result["current"] = parsed.get("current", False)

    # Remaining lines (after first) form the description
    if len(lines) > 1:
        description_lines = lines[1:]

        # Filter out lines that were already parsed as structured fields
        filtered = []
        for dl in description_lines:
            # Skip if this line looks like a duplicate of the first line
            if dl.lower() == first_line.lower():
                continue
            filtered.append(dl)

        result["description"] = " ".join(filtered)

    return result


def parse_experience(raw_text: str) -> List[Dict[str, Any]]:
    """Parse experience section into a list of structured entries.

    Args:
        raw_text: Raw text from the experience section.

    Returns:
        List of dicts with camelCase keys: company, position, location,
        startDate, endDate, current, description.
    """
    if not raw_text or not raw_text.strip():
        return []

    raw_entries = split_entries(raw_text)
    results = [_parse_single_entry(e) for e in raw_entries if e.strip()]

    # Filter out entirely empty entries
    results = [
        r for r in results
        if r.get("company") or r.get("position") or r.get("description")
    ]

    return results
