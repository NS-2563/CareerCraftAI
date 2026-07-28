"""Deterministic summary parser."""


def _normalize_whitespace(text: str) -> str:
    """Collapse multiple whitespace/newlines into single spaces."""
    import re
    return re.sub(r"\s+", " ", text).strip()


def parse_summary(raw_text: str) -> str:
    """Parse and normalize a professional summary.

    Args:
        raw_text: Raw text from the summary section.

    Returns:
        Cleaned and normalized summary string.
    """
    if not raw_text or not raw_text.strip():
        return ""

    return _normalize_whitespace(raw_text)
