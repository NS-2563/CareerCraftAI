"""Deterministic skills section parser."""
import re
from typing import Any, Dict, List


# Pattern for "Category: skill1, skill2, ..."
_CATEGORY_LINE_RE = re.compile(
    r"^\s*(.+?)\s*:\s*(.+)\s*$"
)


def _split_skill_items(text: str) -> List[str]:
    """Split raw skills text into individual skill name fragments."""
    items: List[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        # If line has a colon, it's "Category: skill1, skill2"
        cm = _CATEGORY_LINE_RE.match(stripped)
        if cm:
            # Category itself isn't a skill, but items after colon are
            rest = cm.group(2).strip()
            # Split by comma, bullet, or pipe
            parts = re.split(r"[,;•\|\t]+", rest)
            items.extend(p.strip() for p in parts if p.strip())
        else:
            # Split by comma, bullet, newline, or pipe
            parts = re.split(r"[,;•\|\t]+", stripped)
            items.extend(p.strip() for p in parts if p.strip())

    return items


def _clean_skill_name(name: str) -> str:
    """Clean a single skill name string."""
    name = name.strip().rstrip(".,;:")
    # Remove parenthetical notes like " (Advanced)"
    name = re.sub(r"\s*\(.*?\)\s*$", "", name).strip()
    return name


def parse_skills(raw_text: str) -> List[Dict[str, Any]]:
    """Parse skills section into a list of structured entries.

    Args:
        raw_text: Raw text from the skills section.

    Returns:
        List of dicts with keys: name, level, category.
    """
    if not raw_text or not raw_text.strip():
        return []

    # Extract category-tagged skills from colon lines
    categorized_skills: List[Dict[str, Any]] = []
    uncategorized_items: List[str] = []

    for line in raw_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        cm = _CATEGORY_LINE_RE.match(stripped)
        if cm:
            category = cm.group(1).strip()
            rest = cm.group(2).strip()
            parts = re.split(r"[,;•\|\t]+", rest)
            for part in parts:
                name = _clean_skill_name(part)
                if name:
                    categorized_skills.append({
                        "name": name,
                        "level": "",
                        "category": category,
                    })
        else:
            # Uncategorized line
            parts = re.split(r"[,;•\|\t]+", stripped)
            uncategorized_items.extend(
                _clean_skill_name(p) for p in parts if _clean_skill_name(p)
            )

    # Build result: categorized first, then uncategorized deduped
    seen: set = set()
    result: List[Dict[str, Any]] = []

    for s in categorized_skills:
        key = s["name"].lower()
        if key not in seen:
            seen.add(key)
            result.append(s)

    for name in uncategorized_items:
        key = name.lower()
        if key not in seen:
            seen.add(key)
            result.append({
                "name": name,
                "level": "",
                "category": "",
            })

    return result
