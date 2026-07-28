"""Bullet point quality analysis.

Analyzes work experience and project descriptions for bullet point quality:
- Sentence count per entry
- Whether sentences start with action verbs
- Appropriate sentence length
- Ending punctuation consistency
"""
import re
from typing import Any, Dict, List

from app.analysis.deterministic.action_verbs import _ACTION_VERBS

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_TOO_SHORT_WORDS = 3
_TOO_LONG_WORDS = 50


def _split_sentences(text: str) -> List[str]:
    raw = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]
    result = []
    for s in raw:
        if len(s.split()) >= _TOO_SHORT_WORDS:
            result.append(s)
    return result


def _first_word(sentence: str) -> str:
    words = sentence.strip().split()
    if not words:
        return ""
    return words[0].lower().strip(".,;:!?-'\"")


def analyze_entry_bullets(entry: Dict[str, Any]) -> Dict[str, Any]:
    desc = entry.get("description") or ""
    if not isinstance(desc, str) or not desc.strip():
        return {
            "bullet_count": 0,
            "bullets_with_verb": 0,
            "bullets_too_short": 0,
            "bullets_too_long": 0,
            "bullets_with_period": 0,
            "has_verbs": False,
            "appropriate_length": True,
        }

    sentences = _split_sentences(desc)
    if not sentences:
        sentences = [desc.strip()]

    bullet_count = len(sentences)
    bullets_with_verb = 0
    bullets_too_short = 0
    bullets_too_long = 0
    bullets_with_period = 0

    for s in sentences:
        word_count = len(s.split())
        if word_count < _TOO_SHORT_WORDS:
            bullets_too_short += 1
        if word_count > _TOO_LONG_WORDS:
            bullets_too_long += 1
        if s.endswith(".") or s.endswith("!") or s.endswith("?"):
            bullets_with_period += 1

        first = _first_word(s)
        if first and first in _ACTION_VERBS:
            bullets_with_verb += 1

    return {
        "bullet_count": bullet_count,
        "bullets_with_verb": bullets_with_verb,
        "bullets_too_short": bullets_too_short,
        "bullets_too_long": bullets_too_long,
        "bullets_with_period": bullets_with_period,
        "has_verbs": bullets_with_verb > 0,
        "appropriate_length": bullets_too_short == 0 and bullets_too_long == 0,
    }


def analyze_bullet_quality(resume: Dict[str, Any]) -> Dict[str, Any]:
    total_bullets = 0
    total_with_verb = 0
    total_too_short = 0
    total_too_long = 0
    total_with_period = 0
    entries_with_data = 0
    entries_missing_data = 0

    experience = resume.get("experience") or []
    if not isinstance(experience, list):
        experience = []
    for entry in experience:
        if not isinstance(entry, dict):
            continue
        result = analyze_entry_bullets(entry)
        if result["bullet_count"] > 0:
            entries_with_data += 1
        else:
            entries_missing_data += 1
        total_bullets += result["bullet_count"]
        total_with_verb += result["bullets_with_verb"]
        total_too_short += result["bullets_too_short"]
        total_too_long += result["bullets_too_long"]
        total_with_period += result["bullets_with_period"]

    projects = resume.get("projects") or []
    if not isinstance(projects, list):
        projects = []
    for entry in projects:
        if not isinstance(entry, dict):
            continue
        result = analyze_entry_bullets(entry)
        if result["bullet_count"] > 0:
            entries_with_data += 1
        else:
            entries_missing_data += 1
        total_bullets += result["bullet_count"]
        total_with_verb += result["bullets_with_verb"]
        total_too_short += result["bullets_too_short"]
        total_too_long += result["bullets_too_long"]
        total_with_period += result["bullets_with_period"]

    verb_ratio = round((total_with_verb / total_bullets) * 100, 2) if total_bullets > 0 else 0.0
    period_ratio = round((total_with_period / total_bullets) * 100, 2) if total_bullets > 0 else 0.0

    quality_score = 0
    if total_bullets > 0:
        components = 0.0
        if verb_ratio >= 60:
            components += 30.0
        elif verb_ratio >= 40:
            components += 15.0
        else:
            components += 5.0

        good_length_ratio = 1.0 - ((total_too_short + total_too_long) / total_bullets) if total_bullets > 0 else 0.0
        if good_length_ratio >= 0.9:
            components += 30.0
        elif good_length_ratio >= 0.7:
            components += 15.0
        else:
            components += 5.0

        if period_ratio >= 80:
            components += 20.0
        elif period_ratio >= 50:
            components += 10.0
        else:
            components += 3.0

        if total_bullets >= 10:
            components += 20.0
        elif total_bullets >= 5:
            components += 10.0
        else:
            components += 3.0

        quality_score = min(100, int(components))
        quality_score = max(0, quality_score)

    return {
        "bullet_quality_score": quality_score,
        "total_bullets": total_bullets,
        "entries_with_data": entries_with_data,
        "entries_missing_descriptions": entries_missing_data,
        "bullets_with_verb": total_with_verb,
        "verb_ratio": verb_ratio,
        "bullets_with_period": total_with_period,
        "period_ratio": period_ratio,
        "bullets_too_short": total_too_short,
        "bullets_too_long": total_too_long,
    }
