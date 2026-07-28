"""ATS format and structure analysis — foundation.

Deterministic checks for ATS-friendliness of resume structure.
Phase 3B focuses on reusable architecture; full ATS scoring
is built in Phase 3D.
"""
from typing import Any, Dict, List


_MIN_SECTION_WORDS = 10


def check_section_lengths(resume: Dict[str, Any]) -> Dict[str, Any]:
    results = {}
    total_issues = 0

    summary = resume.get("summary") or ""
    if isinstance(summary, str) and summary.strip():
        wc = len(summary.split())
        if wc < _MIN_SECTION_WORDS:
            total_issues += 1
            results["summary"] = {"word_count": wc, "too_short": True}
        else:
            results["summary"] = {"word_count": wc, "too_short": False}
    else:
        results["summary"] = {"word_count": 0, "too_short": True, "missing": True}
        total_issues += 1

    experience = resume.get("experience") or []
    if not isinstance(experience, list):
        experience = []
    short_exp = 0
    for entry in experience:
        if not isinstance(entry, dict):
            continue
        desc = entry.get("description") or ""
        if isinstance(desc, str) and desc.strip():
            wc = len(desc.split())
            if wc < _MIN_SECTION_WORDS:
                short_exp += 1
        else:
            short_exp += 1
    results["short_experience_entries"] = short_exp
    total_issues += short_exp

    return {
        "section_length_issues": total_issues,
        "details": results,
    }


def check_personal_info(resume: Dict[str, Any]) -> Dict[str, Any]:
    personal = resume.get("personal") or {}
    if not isinstance(personal, dict):
        personal = {}

    has_email = bool(personal.get("email"))
    has_phone = bool(personal.get("phone"))
    has_name = bool(personal.get("first_name") or personal.get("firstName"))
    has_location = bool(personal.get("location"))

    missing = []
    if not has_name:
        missing.append("name")
    if not has_email:
        missing.append("email")
    if not has_phone:
        missing.append("phone")

    return {
        "has_name": has_name,
        "has_email": has_email,
        "has_phone": has_phone,
        "has_location": has_location,
        "missing_fields": missing,
        "ats_complete": len(missing) == 0,
    }
