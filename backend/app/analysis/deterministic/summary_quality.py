"""Summary section quality analysis.

Evaluates resume summary quality beyond word count:
- Length appropriateness (too short, ideal, too long)
- Action verb presence
- Quantifiable metrics presence
- Keyword relevance
- Overall summary quality score
"""
import re
from typing import Any, Dict, List, Set

from app.analysis.deterministic.action_verbs import _ACTION_VERBS

_NUMBER_PATTERN = re.compile(r"\d+")
_CURRENCY_PATTERN = re.compile(r"[\$£€¥]")
_PERCENT_PATTERN = re.compile(r"\d+%")

_IDEAL_MIN_WORDS = 30
_IDEAL_MAX_WORDS = 100


def _count_metrics(text: str) -> Dict[str, int]:
    return {
        "percentages": len(_PERCENT_PATTERN.findall(text)),
        "currency_values": len(_CURRENCY_PATTERN.findall(text)),
        "numbers": len(_NUMBER_PATTERN.findall(text)),
    }


def _find_action_verbs(text: str) -> List[str]:
    text_lower = text.lower()
    found = []
    for verb in sorted(_ACTION_VERBS):
        if verb in text_lower:
            found.append(verb)
    return found


def _find_keywords(text: str, keywords: Set[str]) -> List[str]:
    text_lower = text.lower()
    found = []
    for kw in keywords:
        if kw in text_lower:
            found.append(kw)
    return found


_COMMON_SUMMARY_KEYWORDS = {
    "engineer", "developer", "software", "full-stack", "frontend", "backend",
    "experience", "team", "lead", "technical", "design", "architecture",
    "product", "delivery", "solutions", "innovation", "mentor",
    "full stack", "machine learning", "data", "cloud", "agile",
    "cross-functional", "stakeholder", "results", "impact",
}


def analyze_summary_quality(summary: str) -> Dict[str, Any]:
    if not summary or not isinstance(summary, str) or not summary.strip():
        return {
            "present": False,
            "word_count": 0,
            "length_grade": "missing",
            "has_action_verbs": False,
            "action_verbs_found": [],
            "has_metrics": False,
            "metrics": {"percentages": 0, "currency_values": 0, "numbers": 0},
            "keyword_count": 0,
            "keywords_found": [],
            "summary_quality_score": 0,
        }

    word_count = len(summary.split())

    if word_count < 10:
        length_grade = "very_short"
    elif word_count < _IDEAL_MIN_WORDS:
        length_grade = "short"
    elif word_count <= _IDEAL_MAX_WORDS:
        length_grade = "ideal"
    else:
        length_grade = "long"

    verbs = _find_action_verbs(summary)
    metrics = _count_metrics(summary)
    keywords = _find_keywords(summary, _COMMON_SUMMARY_KEYWORDS)

    has_metrics_flag = (metrics["percentages"] + metrics["currency_values"] + metrics["numbers"]) > 0

    components = 0.0

    if length_grade == "ideal":
        components += 30.0
    elif length_grade == "short":
        components += 15.0
    elif length_grade == "long":
        components += 15.0
    elif length_grade == "very_short":
        components += 5.0

    if len(verbs) >= 2:
        components += 25.0
    elif len(verbs) == 1:
        components += 12.0
    else:
        components += 3.0

    if has_metrics_flag:
        components += 20.0
    else:
        components += 3.0

    if len(keywords) >= 3:
        components += 25.0
    elif len(keywords) == 2:
        components += 15.0
    elif len(keywords) == 1:
        components += 8.0
    else:
        components += 2.0

    quality_score = min(100, int(components))
    quality_score = max(0, quality_score)

    return {
        "present": True,
        "word_count": word_count,
        "length_grade": length_grade,
        "has_action_verbs": len(verbs) > 0,
        "action_verbs_found": verbs,
        "has_metrics": has_metrics_flag,
        "metrics": metrics,
        "keyword_count": len(keywords),
        "keywords_found": keywords,
        "summary_quality_score": quality_score,
    }
