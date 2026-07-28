"""Shared utility functions for resume parsing (no circular dependencies)."""

import re
from typing import Any, Dict, List, Optional, Tuple


_MONTH_NAMES = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}


def normalize_date(text: Optional[str]) -> str:
    """Parse and normalize a date string to YYYY-MM format."""
    if not text or not isinstance(text, str):
        return ""

    text = text.strip()
    if not text:
        return ""

    if text.lower() in ("present", "current", "now", "ongoing"):
        return ""

    # YYYY-MM (ISO)
    m = re.match(r"^(\d{4})\s*-\s*(\d{2})$", text)
    if m:
        return f"{m.group(1)}-{m.group(2)}"

    # MM/YYYY or M/YYYY
    m = re.match(r"^(\d{1,2})\s*/\s*(\d{4})$", text)
    if m:
        month = m.group(1).zfill(2)
        return f"{m.group(2)}-{month}"

    # YYYY (year only)
    m = re.match(r"^(\d{4})$", text)
    if m:
        return m.group(1)

    # "Mon YYYY" or "Month YYYY"
    m = re.match(r"^([A-Za-z]+)\s+(\d{4})$", text)
    if m:
        month_abbr = m.group(1).lower()[:3]
        if month_abbr in _MONTH_NAMES:
            return f"{m.group(2)}-{_MONTH_NAMES[month_abbr]}"

    # "YYYY Mon"
    m = re.match(r"^(\d{4})\s+([A-Za-z]+)$", text)
    if m:
        month_abbr = m.group(2).lower()[:3]
        if month_abbr in _MONTH_NAMES:
            return f"{m.group(1)}-{_MONTH_NAMES[month_abbr]}"

    return text


def parse_date_range(text: Optional[str]) -> Tuple[str, str, bool]:
    """Parse a date range string into (start_date, end_date, current)."""
    if not text or not isinstance(text, str):
        return ("", "", False)

    text = text.strip()

    for sep in (" - ", " – ", "–", "-", " to ", " — "):
        parts = re.split(re.escape(sep), text, maxsplit=1)
        if len(parts) == 2:
            start_raw = parts[0].strip()
            end_raw = parts[1].strip()

            is_current = end_raw.lower() in (
                "present", "current", "now", "ongoing"
            )

            start = normalize_date(start_raw)
            end = "" if is_current else normalize_date(end_raw)

            return (start, end, is_current)

    single = normalize_date(text)
    if single:
        return (single, "", False)

    return ("", "", False)


def normalize_url(text: Optional[str]) -> str:
    """Normalize a URL, adding https:// if missing scheme."""
    if not text or not isinstance(text, str):
        return ""
    text = text.strip()
    if not text:
        return ""
    if text.startswith("http://") or text.startswith("https://"):
        return text
    if "." in text:
        return f"https://{text}"
    return text


def split_entries(text: Optional[str]) -> List[str]:
    """Split section text into individual entries by blank lines."""
    if not text or not text.strip():
        return []

    entries: List[str] = []
    current: List[str] = []

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            if current:
                entries.append("\n".join(current))
                current = []
        else:
            current.append(stripped)

    if current:
        entries.append("\n".join(current))

    return entries


def deduplicate(items: List[Dict], key: str) -> List[Dict]:
    """Remove duplicate items from a list of dicts by a key field."""
    seen: set = set()
    result: List[Dict] = []
    for item in items:
        val = str(item.get(key, "")).strip().lower()
        if val and val not in seen:
            seen.add(val)
            result.append(item)
    return result
