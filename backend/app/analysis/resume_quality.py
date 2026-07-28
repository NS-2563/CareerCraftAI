"""Resume Quality Report — synthesizes deterministic analysis into actionable findings.

Builds on Phase 3B deterministic analyzers to produce:
- Per-section issues, warnings, and strengths
- New missing checks (dates, tech stack, cert dates, resume length)
- Composite section quality scores
- Actionable metadata for frontend consumption

All logic is deterministic and explainable.
"""
from typing import Any, Dict, List, Optional

_SECTIONS_ORDERED = [
    "personal", "summary", "experience", "education", "skills",
    "projects", "certifications", "languages", "interests", "references",
]

_RESUME_LENGTH_IDEAL_MIN = 300
_RESUME_LENGTH_IDEAL_MAX = 700
_RESUME_LENGTH_ACCEPTABLE_MIN = 150
_SUMMARY_IDEAL_MIN = 30
_SUMMARY_IDEAL_MAX = 100
_SKILLS_GOOD_MIN = 5
_BULLET_GOOD_MIN = 10


def _has_value(item: Any) -> bool:
    if item is None:
        return False
    if isinstance(item, str):
        return bool(item.strip())
    if isinstance(item, list):
        return len(item) > 0
    if isinstance(item, dict):
        return any(v is not None and (not isinstance(v, str) or v.strip()) for v in item.values())
    return bool(item)


def _check_experience_dates(experience: List[Dict]) -> List[str]:
    missing = []
    for i, entry in enumerate(experience):
        if not isinstance(entry, dict):
            continue
        has_start = _has_value(entry.get("start_date"))
        has_end = _has_value(entry.get("end_date"))
        has_current = entry.get("current") is True
        if not has_start and not has_end:
            missing.append(f"Entry {i + 1} missing both start and end dates")
        elif not has_start:
            missing.append(f"Entry {i + 1} missing start date")
        elif not has_end and not has_current:
            missing.append(f"Entry {i + 1} missing end date (not marked as current)")
    return missing


def _check_projects_tech_stack(projects: List[Dict]) -> List[str]:
    missing = []
    for i, entry in enumerate(projects):
        if not isinstance(entry, dict):
            continue
        tech = entry.get("techStack") or entry.get("technologies") or entry.get("tech_stack") or []
        has_url = _has_value(entry.get("url")) or _has_value(entry.get("live_url")) or _has_value(entry.get("liveDemo"))
        if not _has_value(tech):
            missing.append(f"Project '{entry.get('name', f'Entry {i + 1}')}' missing technologies")
        if not has_url:
            missing.append(f"Project '{entry.get('name', f'Entry {i + 1}')}' missing URL/live demo")
    return missing


def _check_certifications_details(certifications: List[Dict]) -> List[str]:
    missing = []
    for i, entry in enumerate(certifications):
        if not isinstance(entry, dict):
            continue
        name = entry.get("name", f"Entry {i + 1}")
        if not _has_value(entry.get("issuer")):
            missing.append(f"Certification '{name}' missing issuer")
        if not _has_value(entry.get("date")):
            missing.append(f"Certification '{name}' missing date")
    return missing


def _check_education_dates(education: List[Dict]) -> List[str]:
    missing = []
    for i, entry in enumerate(education):
        if not isinstance(entry, dict):
            continue
        has_start = _has_value(entry.get("start_date"))
        has_end = _has_value(entry.get("end_date"))
        if not has_start:
            missing.append(f"Education entry {i + 1} missing start date")
        if not has_end:
            missing.append(f"Education entry {i + 1} missing end date")
    return missing


def _classify_score(score: int) -> str:
    if score >= 80:
        return "excellent"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    return "poor"


def _invert_score(score: int) -> int:
    return 100 - score


def generate_quality_report(
    resume: Dict[str, Any],
    completeness: Dict[str, Any],
    action_verbs: Any,
    metrics: Dict[str, Any],
    ats_format: Dict[str, Any],
    keywords: Dict[str, Any],
    bullet_quality: Dict[str, Any],
    section_balance: Dict[str, Any],
    summary_quality: Dict[str, Any],
    overall_quality_score: Dict[str, Any],
) -> Dict[str, Any]:
    issues: List[Dict] = []
    warnings: List[Dict] = []
    strengths: List[Dict] = []
    sections: Dict[str, Dict] = {}

    experience_raw = resume.get("experience") or []
    if not isinstance(experience_raw, list):
        experience_raw = []
    projects_raw = resume.get("projects") or []
    if not isinstance(projects_raw, list):
        projects_raw = []
    education_raw = resume.get("education") or []
    if not isinstance(education_raw, list):
        education_raw = []
    certifications_raw = resume.get("certifications") or []
    if not isinstance(certifications_raw, list):
        certifications_raw = []

    # =========================================================================
    # 1. PERSONAL / CONTACT section
    # =========================================================================
    sec: Dict[str, Any] = {"issues": [], "warnings": [], "strengths": [], "score": 100}
    contact = completeness.get("contact", {})
    section_presence = completeness.get("section_presence", {})

    if not section_presence.get("personal"):
        sec["issues"].append("Personal/contact section is missing")
        sec["score"] = 0
    else:
        if not contact.get("has_email"):
            sec["issues"].append("Email address is missing")
            sec["score"] -= 25
        if not contact.get("has_phone"):
            sec["issues"].append("Phone number is missing")
            sec["score"] -= 25
        if not contact.get("has_linkedin"):
            sec["warnings"].append("LinkedIn profile URL is missing")
            sec["score"] -= 10
        if not contact.get("has_github") and not contact.get("has_website"):
            sec["warnings"].append("GitHub and portfolio website are both missing")
            sec["score"] -= 10
        if contact.get("has_email") and contact.get("has_phone") and contact.get("has_name"):
            sec["strengths"].append("Complete contact information provided")
        if contact.get("has_linkedin") or contact.get("has_github") or contact.get("has_website"):
            sec["strengths"].append("Professional online presence included")

    sec["score"] = max(0, min(100, sec["score"]))
    sections["personal"] = sec
    _findings_from_section(issues, warnings, strengths, "personal", sec)

    # =========================================================================
    # 2. SUMMARY section
    # =========================================================================
    sec = {"issues": [], "warnings": [], "strengths": [], "score": 100}
    sq = summary_quality or {}

    if not sq.get("present"):
        sec["issues"].append("Professional summary is missing")
        sec["score"] = 0
    else:
        wc = sq.get("word_count", 0)
        grade = sq.get("length_grade", "missing")
        if grade == "very_short":
            sec["issues"].append(f"Summary is too short ({wc} words, minimum {_SUMMARY_IDEAL_MIN} recommended)")
            sec["score"] -= 30
        elif grade == "short":
            sec["warnings"].append(f"Summary could be expanded ({wc} words, aim for {_SUMMARY_IDEAL_MIN}-{_SUMMARY_IDEAL_MAX})")
            sec["score"] -= 15
        elif grade == "long":
            sec["warnings"].append(f"Summary is long ({wc} words, consider keeping under {_SUMMARY_IDEAL_MAX})")
            sec["score"] -= 10
        else:
            sec["strengths"].append(f"Well-sized summary ({wc} words)")
            sec["score"] += 5

        if sq.get("has_action_verbs"):
            sec["strengths"].append("Summary uses strong action verbs")
        else:
            sec["warnings"].append("Summary lacks strong action verbs")
            sec["score"] -= 15

        if sq.get("has_metrics"):
            sec["strengths"].append("Summary includes quantifiable achievements")
        else:
            sec["warnings"].append("Summary lacks quantified metrics")
            sec["score"] -= 10

        if sq.get("keyword_count", 0) >= 2:
            sec["strengths"].append("Summary contains relevant industry keywords")
        else:
            sec["warnings"].append("Summary could benefit from more relevant keywords")
            sec["score"] -= 10

    sec["score"] = max(0, min(100, sec["score"]))
    sections["summary"] = sec
    _findings_from_section(issues, warnings, strengths, "summary", sec)

    # =========================================================================
    # 3. EXPERIENCE section
    # =========================================================================
    sec = {"issues": [], "warnings": [], "strengths": [], "score": 100}
    sec_completeness = completeness.get("section_completeness", {})
    exp_comp = sec_completeness.get("experience", {})

    if not section_presence.get("experience"):
        sec["issues"].append("Work experience section is missing")
        sec["score"] = 0
    elif len(experience_raw) == 0:
        sec["issues"].append("Work experience section is empty")
        sec["score"] = 0
    else:
        exp_score = exp_comp.get("score", 0)
        if exp_score < 60:
            sec["issues"].append("Experience entries are missing important fields (company, position, dates)")
            sec["score"] -= 30
        elif exp_score < 80:
            sec["warnings"].append("Some experience entries are missing recommended fields")
            sec["score"] -= 15

        av = action_verbs or {}
        if av and isinstance(av, dict):
            total_entries = av.get("total_entries", 0)
            with_verbs = av.get("entries_with_verbs", 0)
            if total_entries > 0:
                verb_ratio = (with_verbs / total_entries) * 100
                if verb_ratio >= 80:
                    sec["strengths"].append("Strong action verb usage across experience entries")
                elif verb_ratio >= 50:
                    sec["warnings"].append(f"Only {with_verbs}/{total_entries} entries use strong action verbs")
                    sec["score"] -= 15
                else:
                    sec["issues"].append(f"Only {with_verbs}/{total_entries} entries use strong action verbs")
                    sec["score"] -= 25

        missing_dates = _check_experience_dates(experience_raw)
        for msg in missing_dates:
            sec["issues"].append(msg)
            sec["score"] -= 20

        bq = bullet_quality or {}
        missing_desc = bq.get("entries_missing_descriptions", 0)
        if missing_desc > 0:
            sec["issues"].append(f"{missing_desc} experience entries are missing descriptions")
            sec["score"] -= missing_desc * 15

        total_bullets = bq.get("total_bullets", 0)
        if total_bullets >= _BULLET_GOOD_MIN:
            sec["strengths"].append(f"Good level of detail ({total_bullets} bullet points across entries)")
        elif total_bullets > 0:
            sec["warnings"].append(f"Consider adding more detail (only {total_bullets} bullet points total)")
            sec["score"] -= 10

        metric_total = metrics.get("total_quantifiable", 0)
        if metric_total >= 3:
            sec["strengths"].append(f"Strong quantifiable achievements ({metric_total} metrics found)")
        elif metric_total > 0:
            sec["warnings"].append(f"Few quantifiable achievements ({metric_total} found, aim for 3+)")
            sec["score"] -= 10
        else:
            sec["warnings"].append("No quantifiable achievements found in experience")
            sec["score"] -= 15

    sec["score"] = max(0, min(100, sec["score"]))
    sections["experience"] = sec
    _findings_from_section(issues, warnings, strengths, "experience", sec)

    # =========================================================================
    # 4. EDUCATION section
    # =========================================================================
    sec = {"issues": [], "warnings": [], "strengths": [], "score": 100}
    edu_comp = sec_completeness.get("education", {})

    if not section_presence.get("education"):
        sec["issues"].append("Education section is missing")
        sec["score"] = 0
    elif len(education_raw) == 0:
        sec["issues"].append("Education section is empty")
        sec["score"] = 0
    else:
        edu_score = edu_comp.get("score", 0)
        if edu_score < 60:
            sec["issues"].append("Education entries are missing important fields (institution, degree, dates)")
            sec["score"] -= 30
        elif edu_score < 80:
            sec["warnings"].append("Some education entries are missing recommended fields")
            sec["score"] -= 15

        edu_date_issues = _check_education_dates(education_raw)
        for msg in edu_date_issues:
            sec["warnings"].append(msg)
            sec["score"] -= 10

        if edu_score >= 80:
            sec["strengths"].append("Complete education entries with all key fields")

    sec["score"] = max(0, min(100, sec["score"]))
    sections["education"] = sec
    _findings_from_section(issues, warnings, strengths, "education", sec)

    # =========================================================================
    # 5. SKILLS section
    # =========================================================================
    sec = {"issues": [], "warnings": [], "strengths": [], "score": 100}
    skills_raw = resume.get("skills") or []
    if not isinstance(skills_raw, list):
        skills_raw = []

    if not section_presence.get("skills"):
        sec["issues"].append("Skills section is missing")
        sec["score"] = 0
    elif len(skills_raw) == 0:
        sec["issues"].append("Skills section is empty")
        sec["score"] = 0
    else:
        skills_with_name = [s for s in skills_raw if isinstance(s, dict) and s.get("name")]
        skill_count = len(skills_with_name)
        if skill_count >= _SKILLS_GOOD_MIN:
            sec["strengths"].append(f"Good skills coverage ({skill_count} skills listed)")
        else:
            sec["warnings"].append(f"Consider listing more skills ({skill_count} found, {_SKILLS_GOOD_MIN}+ recommended)")
            sec["score"] -= 20

        kd = keywords or {}
        matched = kd.get("matched_keywords", [])
        missing_kw = kd.get("missing_common_keywords", [])
        if len(matched) >= 10:
            sec["strengths"].append("Strong keyword coverage matching industry standards")
        elif len(matched) >= 5:
            sec["strengths"].append("Moderate keyword coverage")
        elif len(matched) > 0:
            sec["warnings"].append("Low keyword density — consider adding more relevant technologies")
            sec["score"] -= 15
        if len(missing_kw) > 15:
            sec["warnings"].append(f"{len(missing_kw)} common keywords not found in resume")
            sec["score"] -= 10

    sec["score"] = max(0, min(100, sec["score"]))
    sections["skills"] = sec
    _findings_from_section(issues, warnings, strengths, "skills", sec)

    # =========================================================================
    # 6. PROJECTS section
    # =========================================================================
    sec = {"issues": [], "warnings": [], "strengths": [], "score": 100}
    proj_comp = sec_completeness.get("projects", {})

    if not section_presence.get("projects"):
        sec["warnings"].append("Projects section is missing (optional but recommended)")
        sec["score"] = 70
    elif len(projects_raw) == 0:
        sec["warnings"].append("Projects section is empty")
        sec["score"] = 50
    else:
        proj_score = proj_comp.get("score", 0)
        if proj_score < 60:
            sec["issues"].append("Projects are missing descriptions")
            sec["score"] -= 25

        tech_issues = _check_projects_tech_stack(projects_raw)
        for msg in tech_issues:
            sec["warnings"].append(msg)
            sec["score"] -= 10

        for entry in projects_raw:
            if isinstance(entry, dict) and _has_value(entry.get("description")):
                sec["strengths"].append(f"Project '{entry.get('name', 'unnamed')}' has detailed description")

        proj_entries = len(projects_raw)
        if proj_entries >= 2:
            sec["strengths"].append(f"Good project portfolio ({proj_entries} projects)")

    sec["score"] = max(0, min(100, sec["score"]))
    sections["projects"] = sec
    _findings_from_section(issues, warnings, strengths, "projects", sec)

    # =========================================================================
    # 7. CERTIFICATIONS section
    # =========================================================================
    sec = {"issues": [], "warnings": [], "strengths": [], "score": 100}

    if not section_presence.get("certifications"):
        sec["warnings"].append("Certifications section is missing (optional)")
        sec["score"] = 80
    elif len(certifications_raw) == 0:
        sec["warnings"].append("Certifications section is empty")
        sec["score"] = 70
    else:
        cert_issues = _check_certifications_details(certifications_raw)
        for msg in cert_issues:
            sec["warnings"].append(msg)
            sec["score"] -= 15

        for entry in certifications_raw:
            if isinstance(entry, dict) and _has_value(entry.get("name")) and _has_value(entry.get("issuer")):
                sec["strengths"].append(f"Certification '{entry['name']}' from {entry['issuer']}")

    sec["score"] = max(0, min(100, sec["score"]))
    sections["certifications"] = sec
    _findings_from_section(issues, warnings, strengths, "certifications", sec)

    # =========================================================================
    # 8. LANGUAGES section
    # =========================================================================
    sec = {"issues": [], "warnings": [], "strengths": [], "score": 100}

    if section_presence.get("languages"):
        lang_comp = sec_completeness.get("languages", {})
        lang_count = lang_comp.get("count", 0) if isinstance(lang_comp, dict) else 0
        if lang_count > 0:
            sec["strengths"].append(f"{lang_count} language(s) listed")

    sec["score"] = max(0, min(100, sec["score"]))
    sections["languages"] = sec

    # =========================================================================
    # 9. RESUME LENGTH optimization
    # =========================================================================
    sec_balance = section_balance or {}
    total_words = sec_balance.get("total_words", 0)
    length_findings: Dict[str, Any] = {
        "total_words": total_words,
        "grade": "unknown",
        "recommendation": "",
    }

    if total_words == 0:
        length_findings["grade"] = "empty"
        length_findings["recommendation"] = "Resume has no content"
        issues.append({"type": "issue", "section": "resume_length", "message": "Resume has no content", "details": {"total_words": 0}})
    elif total_words < _RESUME_LENGTH_ACCEPTABLE_MIN:
        length_findings["grade"] = "very_short"
        length_findings["recommendation"] = f"Resume is very short ({total_words} words). Consider expanding to {_RESUME_LENGTH_IDEAL_MIN}-{_RESUME_LENGTH_IDEAL_MAX} words."
        issues.append({
            "type": "issue", "section": "resume_length",
            "message": f"Resume is too short ({total_words} words, {_RESUME_LENGTH_IDEAL_MIN}+ recommended)",
            "details": {"total_words": total_words, "recommended_min": _RESUME_LENGTH_IDEAL_MIN},
        })
    elif total_words < _RESUME_LENGTH_IDEAL_MIN:
        length_findings["grade"] = "short"
        length_findings["recommendation"] = f"Resume is shorter than ideal ({total_words} words). Aim for {_RESUME_LENGTH_IDEAL_MIN}-{_RESUME_LENGTH_IDEAL_MAX} words."
        warnings.append({
            "type": "warning", "section": "resume_length",
            "message": f"Resume could be more detailed ({total_words} words, aim for {_RESUME_LENGTH_IDEAL_MIN}+)",
            "details": {"total_words": total_words, "recommended_min": _RESUME_LENGTH_IDEAL_MIN},
        })
    elif total_words <= _RESUME_LENGTH_IDEAL_MAX:
        length_findings["grade"] = "ideal"
        length_findings["recommendation"] = f"Resume length is optimal ({total_words} words)."
        strengths.append({
            "type": "strength", "section": "resume_length",
            "message": f"Resume length is optimal ({total_words} words)",
            "details": {"total_words": total_words},
        })
    else:
        length_findings["grade"] = "long"
        length_findings["recommendation"] = f"Resume is longer than recommended ({total_words} words). Consider trimming to {_RESUME_LENGTH_IDEAL_MAX} words or fewer."
        warnings.append({
            "type": "warning", "section": "resume_length",
            "message": f"Resume is longer than recommended ({total_words} words, max {_RESUME_LENGTH_IDEAL_MAX})",
            "details": {"total_words": total_words, "recommended_max": _RESUME_LENGTH_IDEAL_MAX},
        })

    # =========================================================================
    # 10. SECTION BALANCE findings
    # =========================================================================
    balance_issues_list = sec_balance.get("balance_issues", [])
    for bi in balance_issues_list:
        warnings.append({
            "type": "warning", "section": "section_balance",
            "message": bi,
            "details": {},
        })

    balance_score_val = sec_balance.get("balance_score", 100)
    if balance_score_val >= 80:
        strengths.append({
            "type": "strength", "section": "section_balance",
            "message": "Well-balanced content across sections",
            "details": {},
        })

    # =========================================================================
    # 11. ATS FORMAT findings
    # =========================================================================
    ats_personal = ats_format.get("personal_info", {})
    if ats_personal.get("ats_complete") is False:
        missing = ats_personal.get("missing_fields", [])
        for field in missing:
            issues.append({
                "type": "issue", "section": "ats_format",
                "message": f"ATS-critical field missing: {field}",
                "details": {"field": field},
            })
    else:
        strengths.append({
            "type": "strength", "section": "ats_format",
            "message": "All ATS-critical fields (name, email, phone) are present",
            "details": {},
        })

    section_length_issues = ats_format.get("section_length_issues", 0)
    if section_length_issues > 0:
        warnings.append({
            "type": "warning", "section": "ats_format",
            "message": f"{section_length_issues} section length issue(s) detected",
            "details": {"count": section_length_issues},
        })

    # =========================================================================
    # 12. OVERALL SCORE AND STATUS
    # =========================================================================
    overall_score = overall_quality_score.get("overall_score", 0)
    status = _classify_score(overall_score)

    total_issues = len(issues)
    total_warnings = len(warnings)
    total_strengths = len(strengths)

    return {
        "overall_score": overall_score,
        "overall_status": status,
        "total_issues": total_issues,
        "total_warnings": total_warnings,
        "total_strengths": total_strengths,
        "issues": issues,
        "warnings": warnings,
        "strengths": strengths,
        "sections": sections,
        "resume_length": length_findings,
    }


def _findings_from_section(
    issues: List[Dict],
    warnings: List[Dict],
    strengths: List[Dict],
    section_name: str,
    section: Dict[str, Any],
) -> None:
    for msg in section.get("issues", []):
        issues.append({"type": "issue", "section": section_name, "message": msg, "details": {}})
    for msg in section.get("warnings", []):
        warnings.append({"type": "warning", "section": section_name, "message": msg, "details": {}})
    for msg in section.get("strengths", []):
        strengths.append({"type": "strength", "section": section_name, "message": msg, "details": {}})


def compute_per_section_quality_scores(
    sections_data: Dict[str, Dict[str, Any]]
) -> Dict[str, int]:
    return {
        name: data.get("score", 0)
        for name, data in sections_data.items()
    }
