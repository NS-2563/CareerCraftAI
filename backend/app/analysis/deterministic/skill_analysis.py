"""Deterministic Skill Analysis — categorizes, normalizes, and enriches skills.

Operates entirely on structured resume data with no AI dependency:
1. Reads the canonical skills section for explicitly listed skills
2. Categorizes each skill using the comprehensive skill catalog
3. Normalizes variant names (JS → JavaScript, Node.js → Node, etc.)
4. Derives skills from certification names where justified
5. Detects implicit skills from experience/project/summary descriptions
6. Produces structured output for downstream gap analysis, JD matching, etc.
"""
from typing import Any, Dict, List, Tuple

from app.analysis.deterministic.skill_catalog import (
    CATEGORY_LABELS,
    _ALL_CANONICAL,
    canonical_display_name,
    find_category,
    get_certification_skills,
    is_known_skill,
    normalize_name,
)


_SOURCE_EXPLICIT = "explicit"
_SOURCE_CERTIFICATION = "certification"
_SOURCE_IMPLICIT = "implicit"

_CONFIDENCE_HIGH = "high"
_CONFIDENCE_MEDIUM = "medium"
_CONFIDENCE_LOW = "low"


def _get_skills_list(resume: Dict[str, Any]) -> List[Any]:
    skills = resume.get("skills") or []
    if not isinstance(skills, list):
        return []
    return skills


def _get_explicit_skills(resume: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    skills = _get_skills_list(resume)
    results = []
    seen_lower: set = set()
    normalizations: Dict[str, str] = {}

    for entry in skills:
        if isinstance(entry, dict):
            raw_name = entry.get("name", "")
            level = entry.get("level", "")
            category = entry.get("category", "")
        elif isinstance(entry, str):
            raw_name = entry
            level = ""
            category = ""
        else:
            continue

        if not isinstance(raw_name, str) or not raw_name.strip():
            continue

        name = raw_name.strip()
        canonical, normalized = normalize_name(name)
        canonical_lower = canonical.lower()

        # Track normalization before dedup so JS→JavaScript is recorded
        # even when "JavaScript" is also explicitly listed
        if normalized:
            normalizations[name] = canonical

        dup_key = canonical_lower
        if dup_key in seen_lower:
            continue
        seen_lower.add(dup_key)

        # Apply canonical display name for case normalization (PYTHON → Python)
        display = canonical_display_name(canonical)

        cat = find_category(canonical)
        results.append({
            "name": display,
            "original_name": name,
            "category_key": cat,
            "category_label": CATEGORY_LABELS.get(cat, cat.replace("_", " ").title()),
            "source": _SOURCE_EXPLICIT,
            "normalized": normalized,
            "confidence": _CONFIDENCE_HIGH,
            "level": level,
            "user_category": category,
        })

    return results, normalizations


def _get_certification_skills(resume: Dict[str, Any]) -> List[Dict[str, Any]]:
    certs = resume.get("certifications") or []
    if not isinstance(certs, list):
        return []

    results = []
    seen_skill_names: set = set()

    for entry in certs:
        if not isinstance(entry, dict):
            continue
        raw_name = entry.get("name", "")
        if not isinstance(raw_name, str) or not raw_name.strip():
            continue

        derived = get_certification_skills(raw_name)
        for skill_name, category in derived:
            dup_key = skill_name.lower().strip()
            if dup_key in seen_skill_names:
                continue
            seen_skill_names.add(dup_key)
            results.append({
                "name": skill_name,
                "original_name": f"from '{raw_name.strip()}'",
                "category_key": category,
                "category_label": CATEGORY_LABELS.get(category, category.replace("_", " ").title()),
                "source": _SOURCE_CERTIFICATION,
                "normalized": False,
                "confidence": _CONFIDENCE_HIGH,
                "level": "",
                "user_category": "",
            })

    return results


def _extract_descriptive_text(resume: Dict[str, Any]) -> str:
    parts = []
    summary = resume.get("summary") or ""
    if isinstance(summary, str) and summary.strip():
        parts.append(summary)

    for section_key in ("experience", "projects"):
        items = resume.get(section_key) or []
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            desc = item.get("description") or ""
            if isinstance(desc, str) and desc.strip():
                parts.append(desc)

    return " ".join(parts)


def _get_implicit_skills(text: str) -> List[Dict[str, Any]]:
    if not text.strip():
        return []

    text_lower = text.lower()
    found: Dict[str, Dict[str, Any]] = {}

    for canonical_name in _ALL_CANONICAL:
        if canonical_name in text_lower:
            cat = find_category(canonical_name)
            display = canonical_display_name(canonical_name)
            found[canonical_name] = {
                "name": display,
                "original_name": canonical_name,
                "category_key": cat,
                "category_label": CATEGORY_LABELS.get(cat, cat.replace("_", " ").title()),
                "source": _SOURCE_IMPLICIT,
                "normalized": False,
                "confidence": _CONFIDENCE_MEDIUM,
                "level": "",
                "user_category": "",
            }

    return list(found.values())


def _merge_skills(
    explicit: List[Dict[str, Any]],
    certification: List[Dict[str, Any]],
    implicit: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    seen: set = set()
    merged: List[Dict[str, Any]] = []

    for skill in explicit:
        key = skill["name"].lower()
        seen.add(key)
        merged.append(skill)

    # Don't dedup cert-derived against explicit — each keeps its source
    for skill in certification:
        key = skill["name"].lower()
        seen.add(key)
        merged.append(skill)

    for skill in implicit:
        key = skill["name"].lower()
        if key not in seen:
            seen.add(key)
            merged.append(skill)

    return merged


def _categorize_skills(skills: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    categories: Dict[str, List[Dict[str, Any]]] = {}
    for cat_key in CATEGORY_LABELS:
        categories[cat_key] = []

    for skill in skills:
        cat_key = skill["category_key"]
        if cat_key in categories:
            categories[cat_key].append(skill)
        else:
            categories.setdefault("uncategorized", []).append(skill)

    return categories


def _compute_sources(skills: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for skill in skills:
        src = skill.get("source", _SOURCE_IMPLICIT)
        counts[src] = counts.get(src, 0) + 1
    return counts


def analyze_skills(resume: Dict[str, Any]) -> Dict[str, Any]:
    """Run deterministic skill analysis on structured resume data.

    Returns categorized, normalized skills with source/confidence metadata.
    """
    explicit, explicit_normalizations = _get_explicit_skills(resume)
    cert_derived = _get_certification_skills(resume)

    desc_text = _extract_descriptive_text(resume)
    implicit = _get_implicit_skills(desc_text)

    all_skills = _merge_skills(explicit, cert_derived, implicit)
    categorized = _categorize_skills(all_skills)
    sources = _compute_sources(all_skills)

    uncategorized = [
        {"name": s["name"], "category_key": s["category_key"]}
        for s in all_skills
        if s["category_key"] == "uncategorized"
    ]

    return {
        "all_skills": all_skills,
        "categorized": categorized,
        "skill_count": len(all_skills),
        "explicit_count": len(explicit),
        "implicit_count": len(implicit),
        "certification_count": len(cert_derived),
        "certification_derived": cert_derived,
        "normalized_skills": explicit_normalizations,
        "uncategorized": [s["name"] for s in uncategorized],
        "sources": sources,
    }
