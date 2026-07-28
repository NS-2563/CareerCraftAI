"""Section and field-level completeness analysis.

Deterministic — operates on structured resume data.
Checks which sections are present and how complete each section is.
"""
from typing import Any, Dict, List


_SECTIONS = [
    "personal",
    "summary",
    "experience",
    "education",
    "skills",
    "projects",
    "certifications",
    "languages",
    "interests",
    "references",
]

_CONTACT_FIELDS = ["email", "phone", "location"]
_CONTACT_ALIASES = {
    "email": ["email"],
    "phone": ["phone"],
    "location": ["location"],
}

_PROFILE_FIELDS = ["linkedin", "github", "website"]
_PROFILE_ALIASES = {
    "linkedin": ["linkedin", "linkedin_url", "linkedIn"],
    "github": ["github", "github_url"],
    "website": ["website", "portfolio", "portfolio_url", "personal_website"],
}

_EDUCATION_FIELDS = ["institution", "degree", "start_date", "end_date"]
_EDUCATION_ALIASES = {
    "institution": ["institution", "school"],
    "degree": ["degree"],
    "start_date": ["start_date", "startDate"],
    "end_date": ["end_date", "endDate"],
}

_EXPERIENCE_FIELDS = ["company", "position", "start_date", "end_date", "description"]
_EXPERIENCE_ALIASES = {
    "company": ["company"],
    "position": ["position", "title"],
    "start_date": ["start_date", "startDate"],
    "end_date": ["end_date", "endDate"],
    "description": ["description"],
}

_PROJECT_FIELDS = ["name", "description"]
_PROJECT_ALIASES = {
    "name": ["name", "title"],
    "description": ["description"],
}

_CERTIFICATION_FIELDS = ["name", "issuer"]
_CERTIFICATION_ALIASES = {
    "name": ["name"],
    "issuer": ["issuer"],
}


def _get_field(item: Any, aliases: List[str]) -> Any:
    if not isinstance(item, dict):
        return None
    for alias in aliases:
        if alias in item and item[alias] is not None:
            val = item[alias]
            if isinstance(val, str) and val.strip():
                return val.strip()
            if not isinstance(val, str):
                return val
    return None


def _has_value(item: Any, aliases: List[str]) -> bool:
    val = _get_field(item, aliases)
    if val is None:
        return False
    if isinstance(val, str) and not val.strip():
        return False
    return True


def _count_present(item: Any, field_aliases: Dict[str, List[str]]) -> int:
    if not isinstance(item, dict):
        return 0
    count = 0
    for aliases in field_aliases.values():
        if _has_value(item, aliases):
            count += 1
    return count


def _is_list_field(resume: dict, key: str, alt_key: str = "") -> List:
    val = resume.get(key)
    if alt_key and val is None:
        val = resume.get(alt_key)
    if val is None:
        return []
    if not isinstance(val, list):
        return []
    return val


def _text_or_none(resume: dict, *keys: str):
    for k in keys:
        val = resume.get(k)
        if val is not None and isinstance(val, str) and val.strip():
            return val.strip()
    return None


def analyze_completeness(resume: Dict[str, Any]) -> Dict[str, Any]:
    section_presence: Dict[str, bool] = {}
    section_completeness: Dict[str, Any] = {}

    summary = _text_or_none(resume, "summary")
    personal_raw = resume.get("personal") or resume.get("personal") or {}
    if not isinstance(personal_raw, dict):
        personal_raw = {}

    experience = _is_list_field(resume, "experience")
    education = _is_list_field(resume, "education")
    skills = _is_list_field(resume, "skills")
    projects = _is_list_field(resume, "projects")
    certifications = _is_list_field(resume, "certifications")
    languages = _is_list_field(resume, "languages")
    interests = _is_list_field(resume, "interests")
    references = _is_list_field(resume, "references")

    section_presence["personal"] = bool(personal_raw.get("first_name") or personal_raw.get("firstName") or personal_raw.get("email"))
    section_presence["summary"] = summary is not None
    section_presence["experience"] = len(experience) > 0
    section_presence["education"] = len(education) > 0
    section_presence["skills"] = len(skills) > 0
    section_presence["projects"] = len(projects) > 0
    section_presence["certifications"] = len(certifications) > 0
    section_presence["languages"] = len(languages) > 0
    section_presence["interests"] = len(interests) > 0
    section_presence["references"] = len(references) > 0

    # Contact info completeness (from personal dict)
    contact_present = 0
    for field, aliases in _CONTACT_ALIASES.items():
        if _has_value(personal_raw, aliases):
            contact_present += 1
    contact_total = len(_CONTACT_FIELDS)
    contact_score = round((contact_present / contact_total) * 100) if contact_total > 0 else 0

    # Profile/online presence (LinkedIn, GitHub, portfolio)
    profile_present = 0
    for field, aliases in _PROFILE_ALIASES.items():
        if _has_value(personal_raw, aliases):
            profile_present += 1
    profile_total = len(_PROFILE_FIELDS)
    profile_score = round((profile_present / profile_total) * 100) if profile_total > 0 else 0

    # Personal completeness
    personal_score = 100 if section_presence["personal"] else 0

    # Summary completeness
    if summary:
        word_count = len(summary.split())
        summary_score = min(100, round((word_count / 30) * 100)) if word_count > 0 else 0
        summary_details = {"word_count": word_count}
    else:
        summary_score = 0
        summary_details = {"word_count": 0}

    # Education completeness
    edu_details = []
    for entry in education:
        present = _count_present(entry, _EDUCATION_ALIASES)
        total = len(_EDUCATION_FIELDS)
        entry_score = round((present / total) * 100) if total > 0 else 0
        edu_details.append({"fields_present": present, "fields_total": total, "completeness": entry_score})
    edu_score = round(sum(e["completeness"] for e in edu_details) / len(edu_details)) if edu_details else 0

    # Experience completeness
    exp_details = []
    for entry in experience:
        present = _count_present(entry, _EXPERIENCE_ALIASES)
        total = len(_EXPERIENCE_FIELDS)
        entry_score = round((present / total) * 100) if total > 0 else 0
        exp_details.append({"fields_present": present, "fields_total": total, "completeness": entry_score})
    exp_score = round(sum(e["completeness"] for e in exp_details) / len(exp_details)) if exp_details else 0

    # Skills completeness
    skills_with_names = [s for s in skills if isinstance(s, dict) and s.get("name")]
    skills_score = min(100, len(skills_with_names) * 10) if skills_with_names else 0

    # Projects completeness
    proj_details = []
    for entry in projects:
        present = _count_present(entry, _PROJECT_ALIASES)
        total = len(_PROJECT_FIELDS)
        entry_score = round((present / total) * 100) if total > 0 else 0
        proj_details.append({"fields_present": present, "fields_total": total, "completeness": entry_score})
    proj_score = round(sum(p["completeness"] for p in proj_details) / len(proj_details)) if proj_details else 0

    # Certifications completeness
    cert_details = []
    for entry in certifications:
        present = _count_present(entry, _CERTIFICATION_ALIASES)
        total = len(_CERTIFICATION_FIELDS)
        entry_score = round((present / total) * 100) if total > 0 else 0
        cert_details.append({"fields_present": present, "fields_total": total, "completeness": entry_score})
    cert_score = round(sum(c["completeness"] for c in cert_details) / len(cert_details)) if cert_details else 0

    # Languages score
    langs_with_value = [l for l in languages if isinstance(l, dict) and l.get("language")]
    langs_score = min(100, len(langs_with_value) * 25) if langs_with_value else 0

    # Aggregated section completeness
    section_completeness = {
        "personal": {"present": section_presence["personal"], "score": personal_score},
        "summary": {"present": section_presence["summary"], "score": summary_score, "details": summary_details},
        "experience": {
            "present": section_presence["experience"],
            "score": exp_score,
            "entry_count": len(experience),
            "entries": exp_details,
        },
        "education": {
            "present": section_presence["education"],
            "score": edu_score,
            "entry_count": len(education),
            "entries": edu_details,
        },
        "skills": {
            "present": section_presence["skills"],
            "score": skills_score,
            "count": len(skills_with_names),
        },
        "projects": {
            "present": section_presence["projects"],
            "score": proj_score,
            "entry_count": len(projects),
            "entries": proj_details,
        },
        "certifications": {
            "present": section_presence["certifications"],
            "score": cert_score,
            "entry_count": len(certifications),
            "entries": cert_details,
        },
        "languages": {
            "present": section_presence["languages"],
            "score": langs_score,
            "count": len(langs_with_value),
        },
        "interests": {
            "present": section_presence["interests"],
            "count": len(interests),
        },
        "references": {
            "present": section_presence["references"],
            "count": len(references),
        },
    }

    # Overall completeness score (weighted average of section presence)
    present_count = sum(1 for v in section_presence.values() if v)
    total_sections = len(_SECTIONS)
    overall_presence_score = round((present_count / total_sections) * 100) if total_sections > 0 else 0

    return {
        "overall_completeness_score": overall_presence_score,
        "section_presence": section_presence,
        "section_completeness": section_completeness,
        "contact": {
            "fields_present": contact_present,
            "fields_total": contact_total,
            "score": contact_score,
            "has_email": _has_value(personal_raw, _CONTACT_ALIASES["email"]),
            "has_phone": _has_value(personal_raw, _CONTACT_ALIASES["phone"]),
            "has_name": bool(personal_raw.get("first_name") or personal_raw.get("firstName")),
            "has_location": _has_value(personal_raw, _CONTACT_ALIASES["location"]),
            "profile_present": profile_present,
            "profile_total": profile_total,
            "profile_score": profile_score,
            "has_linkedin": _has_value(personal_raw, _PROFILE_ALIASES["linkedin"]),
            "has_github": _has_value(personal_raw, _PROFILE_ALIASES["github"]),
            "has_website": _has_value(personal_raw, _PROFILE_ALIASES["website"]),
        },
        "summary_word_count": summary_details["word_count"],
    }
