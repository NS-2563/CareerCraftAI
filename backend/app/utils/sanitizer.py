import re


BLOCKED_PATTERNS = [
    re.compile(r"</?script[^>]*/?>", re.IGNORECASE),
    re.compile(r"</?iframe[^>]*/?>", re.IGNORECASE),
    re.compile(r"</?object[^>]*/?>", re.IGNORECASE),
    re.compile(r"<embed[^>]*/?>", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"data\s*:\s*text/html", re.IGNORECASE),
]


CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def strip_blocked_patterns(text: str) -> str:
    for pattern in BLOCKED_PATTERNS:
        text = pattern.sub("", text)
    return text


def strip_control_chars(text: str) -> str:
    return CONTROL_CHARS.sub("", text)


def sanitize_ai_output(text: str | None, max_length: int = 50000) -> str | None:
    if text is None:
        return None
    text = strip_control_chars(text)
    text = strip_blocked_patterns(text)
    if len(text) > max_length:
        text = text[:max_length]
    return text


def sanitize_ai_output_list(items: list[str] | None) -> list[str] | None:
    if items is None:
        return None
    return [sanitize_ai_output(item) for item in items]
