"""Deterministic references section parser."""
import re
from typing import Any, Dict, List

from app.resume.services.parser_utils import split_entries


# Email pattern
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

# Phone pattern
_PHONE_RE = re.compile(r"\+?\(?\d[\d\s().-]{6,}\d")


def _parse_single_entry(text: str) -> Dict[str, Any]:
    """Parse a single reference entry.

    Returns dict with keys: name, designation, organization, email, phone.
    """
    result: Dict[str, Any] = {
        "name": "",
        "designation": "",
        "organization": "",
        "email": "",
        "phone": "",
    }

    if not text or not text.strip():
        return result

    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if not lines:
        return result

    # Extract email from anywhere
    email = ""
    for line in lines:
        em = _EMAIL_RE.search(line)
        if em:
            email = em.group(0).strip().lower()
            break

    # Extract phone from anywhere
    phone = ""
    for line in lines:
        pm = _PHONE_RE.search(line)
        if pm:
            phone = pm.group(0).strip()
            break

    # Name is typically the first line
    # If first line contains email, look at second line
    first_line = lines[0]
    if "@" in first_line and len(lines) > 1:
        result["name"] = lines[1]
    else:
        result["name"] = first_line

    result["email"] = email
    result["phone"] = phone

    # Second (or third) line often has "Designation at Organization"
    title_line = ""
    for i, l in enumerate(lines):
        if i == 0 and "@" in l:
            continue
        if i == 0 and l == result["name"]:
            continue
        if not title_line and "@" not in l and l != phone:
            title_line = l
            break

    if title_line:
        # Try "Designation at Organization" or "Designation, Organization"
        at_match = re.match(r"^\s*(.+?)\s+at\s+(.+?)\s*$", title_line, re.IGNORECASE)
        if at_match:
            result["designation"] = at_match.group(1).strip()
            result["organization"] = at_match.group(2).strip()
        else:
            # Try comma separation
            comma_match = re.match(r"^\s*(.+?),\s*(.+?)\s*$", title_line)
            if comma_match:
                result["designation"] = comma_match.group(1).strip()
                result["organization"] = comma_match.group(2).strip()
            else:
                result["designation"] = title_line

    return result


def parse_references(raw_text: str) -> List[Dict[str, Any]]:
    """Parse references section into a list of structured entries.

    Args:
        raw_text: Raw text from the references section.

    Returns:
        List of dicts with keys: name, designation, organization,
        email, phone.
    """
    if not raw_text or not raw_text.strip():
        return []

    # "Available upon request" — skip, no structured data
    lower = raw_text.strip().lower()
    if "available upon request" in lower or "available on request" in lower:
        return []

    raw_entries = split_entries(raw_text)
    results = [_parse_single_entry(e) for e in raw_entries if e.strip()]

    results = [r for r in results if r.get("name")]

    return results
