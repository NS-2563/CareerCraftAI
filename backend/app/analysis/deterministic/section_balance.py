"""Section balance analysis.

Analyzes content distribution across resume sections:
- Word count per section
- Percentage of total content per section
- Balance scoring (penalizes single-section dominance)
- Section ordering conventions
"""
from typing import Any, Dict, List


_SECTION_ORDER = ["summary", "experience", "education", "skills", "projects", "certifications"]


def _count_section_words(resume: Dict[str, Any], section: str) -> int:
    if section == "summary":
        val = resume.get("summary") or ""
        if isinstance(val, str):
            return len(val.split())
        return 0

    items = resume.get(section) or []
    if not isinstance(items, list):
        return 0
    total = 0
    for entry in items:
        if not isinstance(entry, dict):
            if isinstance(entry, str):
                total += len(entry.split())
            continue
        for field in ("description", "name", "degree", "position", "summary"):
            val = entry.get(field) or ""
            if isinstance(val, str):
                total += len(val.split())
    return total


def analyze_section_balance(resume: Dict[str, Any]) -> Dict[str, Any]:
    sections = {
        "summary": _count_section_words(resume, "summary"),
        "experience": _count_section_words(resume, "experience"),
        "education": _count_section_words(resume, "education"),
        "projects": _count_section_words(resume, "projects"),
        "skills": _count_section_words(resume, "skills"),
        "certifications": _count_section_words(resume, "certifications"),
    }

    present_sections = {k: v for k, v in sections.items() if v > 0}
    total_words = sum(present_sections.values())

    if total_words == 0:
        return {
            "section_word_counts": sections,
            "total_words": 0,
            "section_percentages": {k: 0.0 for k in sections},
            "present_sections": list(present_sections.keys()),
            "balance_issues": ["No content found in any section"],
            "dominant_section": None,
            "balance_score": 0,
            "section_count": 0,
        }

    percentages = {}
    for k in sections:
        percentages[k] = round((sections[k] / total_words) * 100, 2)

    issues = []
    for section, pct in percentages.items():
        if pct > 70:
            issues.append(f"{section} dominates with {pct}% of content")
        elif pct > 50:
            issues.append(f"{section} is over half ({pct}%) of content")

    dominant = max(sections, key=sections.get) if present_sections else None
    max_pct = percentages.get(dominant, 0) if dominant else 0

    if len(present_sections) <= 1:
        balance_score = 10
    elif max_pct > 70:
        balance_score = 30
    elif max_pct > 50:
        balance_score = 50
    elif max_pct > 40:
        balance_score = 70
    elif len(present_sections) >= 4:
        balance_score = 90
    else:
        balance_score = 80

    if "summary" in present_sections:
        summary_pct = percentages.get("summary", 0)
        if summary_pct > 40:
            balance_score = max(10, balance_score - 20)
            issues.append("Summary section is disproportionately large")

    return {
        "section_word_counts": sections,
        "total_words": total_words,
        "section_percentages": percentages,
        "present_sections": sorted(present_sections.keys()),
        "balance_issues": issues,
        "dominant_section": dominant,
        "balance_score": balance_score,
        "section_count": len(present_sections),
    }
