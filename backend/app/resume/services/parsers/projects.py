"""Deterministic projects section parser."""
import re
from typing import Any, Dict, List

from app.resume.services.parser_utils import (
    normalize_url,
    split_entries,
)


# URL patterns
_GITHUB_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/[\w-]+(?:/[\w.-]+)?",
    re.IGNORECASE,
)
_GENERIC_URL_RE = re.compile(r"https?://[^\s,;)]+")


def _extract_urls(text: str) -> Dict[str, str]:
    """Extract GitHub URL and other URLs from text."""
    github = ""
    live = ""

    github_m = _GITHUB_URL_RE.search(text)
    if github_m:
        github = github_m.group(0).strip().rstrip("/")

    # Find non-github URLs
    for m in _GENERIC_URL_RE.finditer(text):
        url = m.group(0).strip().rstrip("/").rstrip(")")
        if "github" not in url.lower() and not live:
            live = url
        if github and live:
            break

    return {"github": github, "live": live}


def _extract_tech_stack(text: str) -> str:
    """Extract technology / tech stack mentions from text."""
    tech_keywords = [
        r"built\s+(?:with|using)",
        r"technologies?\s*(?::|used)",
        r"tech\s*stack\s*(?::|used)",
        r"tools?\s*(?::|used)",
        r"stack\s*(?::|used)",
    ]

    for kw in tech_keywords:
        m = re.search(kw + r"\s*(.+)", text, re.IGNORECASE)
        if m:
            result = m.group(1).strip()
            # Cut at a period followed by space + word (sentence boundary)
            cut = re.search(r"\.\s+[a-zA-Z]", result)
            if cut:
                result = result[:cut.start()]
            return result.strip("., ")

    return ""


def _parse_single_entry(text: str) -> Dict[str, Any]:
    """Parse a single project entry.

    Returns dict with camelCase keys: title, techStack, github,
    liveDemo, description.
    """
    result: Dict[str, Any] = {
        "title": "",
        "techStack": "",
        "github": "",
        "liveDemo": "",
        "description": "",
    }

    if not text or not text.strip():
        return result

    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if not lines:
        return result

    # First line is the title
    result["title"] = lines[0]

    # Extract URLs from all lines
    all_text = " ".join(lines)
    urls = _extract_urls(all_text)
    result["github"] = normalize_url(urls["github"])
    result["liveDemo"] = normalize_url(urls["live"])

    # Extract tech stack
    tech_stack = _extract_tech_stack(all_text)
    if tech_stack:
        result["techStack"] = tech_stack

    # Build description from remaining lines (excluding title)
    desc_lines = []
    for l in lines[1:]:
        # Skip lines that are just URLs or tech stack indicators
        if _GENERIC_URL_RE.match(l):
            continue
        lower = l.lower()
        if any(kw.replace("\\s*", " ") in lower.replace("\\", "") for kw in
               ["built with", "technologies", "tech stack", "stack:"]):
            continue
        desc_lines.append(l)

    if desc_lines:
        result["description"] = " ".join(desc_lines)

    return result


def parse_projects(raw_text: str) -> List[Dict[str, Any]]:
    """Parse projects section into a list of structured entries.

    Args:
        raw_text: Raw text from the projects section.

    Returns:
        List of dicts with camelCase keys: title, techStack, github,
        liveDemo, description.
    """
    if not raw_text or not raw_text.strip():
        return []

    raw_entries = split_entries(raw_text)
    results = [_parse_single_entry(e) for e in raw_entries if e.strip()]

    results = [
        r for r in results if r.get("title") or r.get("description")
    ]

    return results
