"""Deterministic personal information parser."""
import re
from typing import Dict, List, Optional

from app.resume.services.parser_utils import normalize_url


_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(
    r"\+?\(?\d[\d\s().-]{6,}\d"
)
_LINKEDIN_RE = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+[/]?",
    re.IGNORECASE,
)
_GITHUB_RE = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/[\w-]+/?",
    re.IGNORECASE,
)
_URL_RE = re.compile(r"https?://[^\s]+")
_BARE_URL_RE = re.compile(r"(?:https?://)?[\w-]+\.[a-zA-Z]{2,}(?:/[\w\-./?=]+)?")
_NAME_LINE_RE = re.compile(
    r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}$"
)


def _extract_email(text: str) -> str:
    m = _EMAIL_RE.search(text)
    return m.group(0).strip().lower() if m else ""


def _extract_phone(text: str) -> str:
    m = _PHONE_RE.search(text)
    return m.group(0).strip() if m else ""


def _extract_urls(text: str) -> Dict[str, str]:
    """Extract LinkedIn, GitHub, and generic URLs from text."""
    linkedin = ""
    github = ""
    portfolio = ""

    lines = text.split("\n")
    for line in lines:
        lower = line.lower()
        lm = _LINKEDIN_RE.search(line)
        if lm and not linkedin:
            linkedin = lm.group(0).strip().rstrip("/")
        gm = _GITHUB_RE.search(line)
        if gm and not github:
            github = gm.group(0).strip().rstrip("/")

    # Fallback: generic URL that isn't LinkedIn or GitHub
    for line in lines:
        if "@" in line:
            continue
        url = ""
        um = _URL_RE.search(line)
        if um:
            url = um.group(0).strip()
        else:
            bm = _BARE_URL_RE.match(line)
            if bm:
                url = bm.group(0).strip()
        if url:
            url = url.rstrip("/").rstrip(")")
            if "linkedin" not in url.lower() and "github" not in url.lower():
                if not portfolio:
                    portfolio = url

    return {
        "linkedin": linkedin,
        "github": github,
        "portfolio": portfolio,
    }


def _try_split_name(name: str) -> tuple:
    """Try to split a full name into first and last name."""
    parts = name.strip().split(None, 1)
    if len(parts) == 2:
        return (parts[0], parts[1])
    if len(parts) == 1:
        return (parts[0], "")
    return ("", "")


def _find_name_line(lines: List[str], used_indices: set) -> tuple:
    """Find the most likely name line from header text.

    Returns (name_str, index) or ("", -1).
    """
    for i, line in enumerate(lines):
        if i in used_indices:
            continue
        stripped = line.strip()
        if not stripped:
            continue
        if "@" in stripped:
            continue
        if re.search(r"\d", stripped) and len(stripped) > 3:
            continue
        if stripped.startswith("http"):
            continue
        if len(stripped.split()) >= 2 and _NAME_LINE_RE.match(stripped):
            used_indices.add(i)
            return (stripped, i)

    for i, line in enumerate(lines):
        if i in used_indices:
            continue
        stripped = line.strip()
        if not stripped:
            continue
        if "@" in stripped:
            continue
        if len(stripped) > 3 and stripped[0].isupper():
            used_indices.add(i)
            return (stripped, i)

    return ("", -1)


def _find_location(lines: List[str], used_indices: set) -> str:
    """Find a location string from header lines."""
    loc_patterns = [
        re.compile(r"^[A-Za-z\s]+,\s*[A-Z]{2}\b"),  # "City, ST"
        re.compile(r"^[A-Za-z\s]+,\s*[A-Za-z\s]+"),  # "City, Country"
    ]
    for i, line in enumerate(lines):
        if i in used_indices:
            continue
        stripped = line.strip()
        if not stripped:
            continue
        # Must contain letters and comma/state pattern
        for pat in loc_patterns:
            if pat.match(stripped):
                used_indices.add(i)
                return stripped

    return ""


def _find_title(lines: List[str], name_index: int, used_indices: set) -> str:
    """Find the professional title, typically on the line after the name."""
    for i in range(name_index + 1, min(name_index + 3, len(lines))):
        if i in used_indices:
            continue
        stripped = lines[i].strip()
        if not stripped:
            continue
        if "@" in stripped:
            continue
        if stripped.startswith("http"):
            continue
        if len(stripped) < 80:
            used_indices.add(i)
            return stripped
    return ""


def parse_personal(raw_text: str) -> Dict[str, str]:
    """Extract structured personal information from header text.

    Args:
        raw_text: Raw text from the header section (before first heading).

    Returns:
        Dict with camelCase keys: firstName, lastName, title, email,
        phone, location, linkedin, github, portfolio.
    """
    result: Dict[str, str] = {
        "firstName": "",
        "lastName": "",
        "title": "",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin": "",
        "github": "",
        "portfolio": "",
    }

    if not raw_text or not raw_text.strip():
        return result

    lines = raw_text.strip().split("\n")
    stripped_lines = [l.strip() for l in lines if l.strip()]
    used_indices: set = set()

    # Extract contact info first (non-exclusive)
    full_text = " ".join(stripped_lines)
    email = _extract_email(full_text)
    phone = _extract_phone(full_text)
    urls = _extract_urls(raw_text)

    # Mark lines that were used by contact info
    for i, line in enumerate(stripped_lines):
        if email and email in line:
            used_indices.add(i)
        if phone and phone in line:
            used_indices.add(i)
        for url_key, url_val in urls.items():
            if url_val and url_val.rstrip("/") in line.rstrip("/"):
                used_indices.add(i)

    # Extract name
    name, name_idx = _find_name_line(stripped_lines, used_indices)
    first_name, last_name = _try_split_name(name)

    # Extract location
    location = _find_location(stripped_lines, used_indices)

    # Extract title (line after name, if not used)
    title = ""
    if name and name_idx >= 0:
        title = _find_title(stripped_lines, name_idx, used_indices)

    result["firstName"] = first_name
    result["lastName"] = last_name
    result["title"] = title
    result["email"] = email
    result["phone"] = phone
    result["location"] = location
    result["linkedin"] = normalize_url(urls["linkedin"])
    result["github"] = normalize_url(urls["github"])
    result["portfolio"] = normalize_url(urls["portfolio"])

    return result
