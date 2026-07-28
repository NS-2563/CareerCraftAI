"""Deterministic interests section parser."""
import re
from typing import Any, Dict, List


def parse_interests(raw_text: str) -> List[Dict[str, Any]]:
    """Parse interests section into a list of entries.

    Supports comma-separated, newline-separated, and bullet lists.

    Args:
        raw_text: Raw text from the interests section.

    Returns:
        List of dicts with key: name.
    """
    if not raw_text or not raw_text.strip():
        return []

    seen: set = set()
    results: List[Dict[str, Any]] = []

    for line in raw_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        # Split by comma, bullet, or pipe
        parts = re.split(r"[,;•\|\t]+", stripped)
        for part in parts:
            name = part.strip().strip(".- \t")
            if not name:
                continue
            key = name.lower()
            if key not in seen:
                seen.add(key)
                results.append({"name": name})

    return results
