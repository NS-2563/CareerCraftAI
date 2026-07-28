"""Deterministic certifications section parser."""
import re
from typing import Any, Dict, List

from app.resume.services.parser_utils import (
    normalize_date,
    normalize_url,
    split_entries,
)


# Common patterns for certification first lines
_ISSUER_RE = re.compile(
    r"^\s*(.+?)\s*[–\-—|]\s*(.+?)\s*$"
)

# Pattern: name | issuer | date/url
_THREE_PART_RE = re.compile(
    r"^\s*(.+?)\s*[|]\s*(.+?)\s*[|]\s*(.+?)\s*$"
)

# Date pattern
_DATE_RE = re.compile(
    r"\b(\d{4}|\w+\s+\d{4}|\d{1,2}/\d{4})\b"
)

# URL pattern
_URL_RE = re.compile(r"https?://[^\s,;)]+")


def _parse_single_entry(text: str) -> Dict[str, Any]:
    """Parse a single certification entry.

    Returns dict with camelCase keys: name, issuer, issueDate,
    credentialUrl.
    """
    result: Dict[str, Any] = {
        "name": "",
        "issuer": "",
        "issueDate": "",
        "credentialUrl": "",
    }

    if not text or not text.strip():
        return result

    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if not lines:
        return result

    # First line: "Cert Name — Issuer" or "Cert Name | Issuer" or "Name | Issuer | Date"
    first = lines[0]
    three_match = _THREE_PART_RE.match(first)
    if three_match:
        result["name"] = three_match.group(1).strip()
        result["issuer"] = three_match.group(2).strip()
        third = three_match.group(3).strip()
        dm = _DATE_RE.match(third)
        if dm:
            result["issueDate"] = normalize_date(dm.group(1).strip())
    else:
        issuer_match = _ISSUER_RE.match(first)
        if issuer_match:
            result["name"] = issuer_match.group(1).strip()
            result["issuer"] = issuer_match.group(2).strip()
        else:
            result["name"] = first

    # Search all lines for date
    for line in lines:
        dm = _DATE_RE.search(line)
        if dm:
            result["issueDate"] = normalize_date(dm.group(1).strip())
            break

    # Search all lines for URL
    for line in lines:
        um = _URL_RE.search(line)
        if um:
            result["credentialUrl"] = normalize_url(um.group(0).strip())
            break

    return result


def parse_certifications(raw_text: str) -> List[Dict[str, Any]]:
    """Parse certifications section into a list of structured entries.

    Args:
        raw_text: Raw text from the certifications section.

    Returns:
        List of dicts with camelCase keys: name, issuer, issueDate,
        credentialUrl.
    """
    if not raw_text or not raw_text.strip():
        return []

    raw_entries = split_entries(raw_text)
    results = [_parse_single_entry(e) for e in raw_entries if e.strip()]

    results = [
        r for r in results if r.get("name") or r.get("issuer")
    ]

    return results
