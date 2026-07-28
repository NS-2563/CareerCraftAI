"""Quantifiable achievement/metric detection.

Deterministic — detects numbers, percentages, currency, and measurable
outcomes in resume description text.
"""
import re
from typing import Any, Dict, List


_PERCENTAGE_PATTERN = re.compile(r"\b\d+([.,]\d+)?\s*%")
_CURRENCY_PATTERN = re.compile(r"[$£€]\s*\d+([.,]\d+)*(K|M|B|k|m|b)?\b")
_NUMBER_PATTERN = re.compile(r"\b\d{2,}(?:[.,]\d+)?(?:[KMBkmb])?\b")
_TIME_PATTERN = re.compile(
    r"\b(\d+[-\s]?(year|month|week|day|hour)[s]?)\b",
    re.IGNORECASE,
)
_MAGNITUDE_WORDS = [
    "increased", "decreased", "reduced", "improved", "grew", "raised",
    "doubled", "tripled", "saved", "generated", "delivered", "achieved",
    "exceeded", "surpassed", "boosted", "cut", "lowered", "accelerated",
    "expanded", "grew", "led", "managed", "handled", "produced",
    "processed", "served", "supported",
]


def detect_percentages(text: str) -> List[str]:
    if not text:
        return []
    return [m.group(0) for m in _PERCENTAGE_PATTERN.finditer(text)]


def detect_currency(text: str) -> List[str]:
    if not text:
        return []
    return [m.group(0) for m in _CURRENCY_PATTERN.finditer(text)]


def detect_numbers(text: str) -> List[str]:
    if not text:
        return []
    return [m.group(0) for m in _NUMBER_PATTERN.finditer(text)]


def detect_time_metrics(text: str) -> List[str]:
    if not text:
        return []
    return [m.group(0) for m in _TIME_PATTERN.finditer(text)]


def detect_magnitude_words(text: str) -> List[str]:
    if not text:
        return []
    pattern = re.compile(
        r"\b(" + "|".join(_MAGNITUDE_WORDS) + r")\b",
        re.IGNORECASE,
    )
    seen = set()
    result = []
    for m in pattern.finditer(text):
        lower = m.group(0).lower()
        if lower not in seen:
            seen.add(lower)
            result.append(m.group(0))
    return result


def analyze_metrics(experience: List[Dict[str, Any]], projects: List[Dict[str, Any]], summary: str = None) -> Dict[str, Any]:
    all_text = ""
    if summary:
        all_text += summary + " "

    for entry in (experience or []):
        if isinstance(entry, dict):
            desc = entry.get("description") or ""
            all_text += desc + " "

    for entry in (projects or []):
        if isinstance(entry, dict):
            desc = entry.get("description") or ""
            all_text += desc + " "

    percentages = detect_percentages(all_text)
    currencies = detect_currency(all_text)
    numbers = detect_numbers(all_text)
    time_metrics = detect_time_metrics(all_text)
    magnitude_words = detect_magnitude_words(all_text)

    return {
        "percentages": percentages,
        "currency_values": currencies,
        "numbers": numbers,
        "time_metrics": time_metrics,
        "magnitude_words": magnitude_words,
        "total_quantifiable": len(percentages) + len(currencies) + len(time_metrics),
    }
