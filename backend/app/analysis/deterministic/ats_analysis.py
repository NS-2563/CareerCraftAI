"""ATS Analysis — unified deterministic ATS compatibility scoring layer.

Builds on Phase 3B/3C analyzers to produce a comprehensive ATS assessment:
- 5-component scoring model (Structure, Keywords, Action Verbs, Quantified Impact, Contact Info)
- Risk level classification with specific risk factors
- Actionable, prioritized recommendations
- ATS-specific findings (issues, warnings, strengths)

All logic is deterministic, explainable, and reuses existing analyzer outputs.
"""
import re
from typing import Any, Dict, List, Optional, Tuple


_EXPECTED_SECTION_ORDER = ["summary", "experience", "education", "skills", "projects", "certifications"]

_DATE_PATTERNS = [
    (r"^\d{4}-\d{2}$", "YYYY-MM"),
    (r"^\d{4}$", "YYYY"),
    (r"^\d{2}/\d{4}$", "MM/YYYY"),
    (r"^\d{2}/\d{2}/\d{4}$", "MM/DD/YYYY"),
    (r"^[A-Z][a-z]+ \d{4}$", "Month YYYY"),
]

_STRUCTURE_WEIGHT = 0.25
_KEYWORDS_WEIGHT = 0.20
_ACTION_VERBS_WEIGHT = 0.20
_QUANTIFIED_WEIGHT = 0.20
_CONTACT_WEIGHT = 0.15


def _detect_date_format(date_str: str) -> Optional[str]:
    if not isinstance(date_str, str) or not date_str.strip():
        return None
    for pattern, label in _DATE_PATTERNS:
        if re.match(pattern, date_str.strip()):
            return label
    return None


def _detect_section_order(resume: Dict[str, Any]) -> List[str]:
    order = []
    for key in resume:
        if key in _EXPECTED_SECTION_ORDER:
            order.append(key)
    remaining = [s for s in _EXPECTED_SECTION_ORDER if s in resume and s not in order]
    order.extend(remaining)
    return order


def _check_section_ordering(resume: Dict[str, Any]) -> Tuple[bool, List[str]]:
    present_order = _detect_section_order(resume)
    present_set = set(present_order)
    issues = []
    has_deviation = False

    if "summary" in present_set and present_order[0] != "summary":
        has_deviation = True
        issues.append(f"Summary should appear first, found '{present_order[0]}' first")

    for i, section in enumerate(present_order):
        if section not in _EXPECTED_SECTION_ORDER:
            continue
        expected_idx = _EXPECTED_SECTION_ORDER.index(section)
        for j in range(i):
            earlier = present_order[j]
            if earlier in _EXPECTED_SECTION_ORDER:
                earlier_idx = _EXPECTED_SECTION_ORDER.index(earlier)
                if earlier_idx > expected_idx:
                    has_deviation = True
                    issues.append(f"'{earlier}' appears before '{section}', expected '{_EXPECTED_SECTION_ORDER[earlier_idx]}' before '{_EXPECTED_SECTION_ORDER[expected_idx]}'")
                    break

    return has_deviation, issues


def _compute_skills_keyword_alignment(skills_list: Any, matched_keywords: List[str]) -> float:
    if not skills_list or not matched_keywords:
        return 0.0
    skill_names = set()
    for s in skills_list:
        if isinstance(s, dict):
            name = s.get("name", "")
        elif isinstance(s, str):
            name = s
        else:
            continue
        if name and isinstance(name, str):
            skill_names.add(name.lower().strip())
    if not skill_names:
        return 0.0
    matched_lower = set(k.lower() for k in matched_keywords)
    overlap = skill_names & matched_lower
    return round((len(overlap) / len(skill_names)) * 100, 1)


def _compute_bullet_consistency(experience: List[Dict], projects: List[Dict]) -> Tuple[float, str]:
    bullet_lengths = []
    for entry in (experience or []) + (projects or []):
        if not isinstance(entry, dict):
            continue
        desc = entry.get("description") or ""
        if not isinstance(desc, str) or not desc.strip():
            continue
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", desc) if s.strip()]
        for s in sentences:
            wc = len(s.split())
            if wc >= 3:
                bullet_lengths.append(wc)

    if len(bullet_lengths) < 3:
        return 0.0, "insufficient_data"

    mean = sum(bullet_lengths) / len(bullet_lengths)
    variance = sum((x - mean) ** 2 for x in bullet_lengths) / len(bullet_lengths)
    std_dev = variance ** 0.5

    if std_dev <= 8:
        return round(std_dev, 1), "consistent"
    elif std_dev <= 15:
        return round(std_dev, 1), "moderate"
    else:
        return round(std_dev, 1), "inconsistent"


def _compute_date_consistency(resume: Dict[str, Any]) -> Tuple[Optional[str], List[str]]:
    all_formats = []
    issues = []
    for section, date_fields in [("experience", ["start_date", "end_date"]), ("education", ["start_date", "end_date"]), ("certifications", ["date"])]:
        items = resume.get(section) or []
        if not isinstance(items, list):
            continue
        for entry in items:
            if not isinstance(entry, dict):
                continue
            for field in date_fields:
                val = entry.get(field) or ""
                fmt = _detect_date_format(val)
                if fmt:
                    all_formats.append((section, field, val, fmt))

    if not all_formats:
        return None, issues

    unique_formats = set(f for _, _, _, f in all_formats)
    if len(unique_formats) == 0:
        return None, issues
    if len(unique_formats) == 1:
        return list(unique_formats)[0], issues

    format_counts: Dict[str, int] = {}
    for _, _, _, fmt in all_formats:
        format_counts[fmt] = format_counts.get(fmt, 0) + 1

    dominant = max(format_counts, key=format_counts.get)
    mixeds = [(s, fld, val, fmt) for s, fld, val, fmt in all_formats if fmt != dominant]
    for section, field, val, fmt in mixeds[:5]:
        issues.append(f"Inconsistent date format '{fmt}' in {section}.{field}: '{val}' (expected '{dominant}')")

    return dominant, issues


def _compute_quantified_ratio(metrics: Dict[str, Any], bullet_quality: Dict[str, Any]) -> float:
    total_metrics = metrics.get("total_quantifiable", 0)
    total_bullets = bullet_quality.get("total_bullets", 0)
    if total_bullets == 0:
        return 0.0
    return round((total_metrics / total_bullets) * 100, 1)


def _score_structure(
    resume: Dict[str, Any],
    completeness: Dict[str, Any],
    ats_format: Dict[str, Any],
    section_balance: Dict[str, Any],
    summary_quality: Dict[str, Any],
) -> Tuple[int, Dict[str, Any], List[str], List[str]]:
    issues: List[str] = []
    strengths: List[str] = []
    score = 0
    max_score = 100
    details: Dict[str, Any] = {}

    section_presence = completeness.get("section_presence", {})
    key_sections = ["summary", "experience", "education", "skills"]
    present_count = sum(1 for s in key_sections if section_presence.get(s))
    if present_count >= 4:
        score += 40
        strengths.append("All key sections (summary, experience, education, skills) are present")
    elif present_count >= 3:
        score += 25
        issues.append(f"One key section missing ({4 - present_count} of 4 present)")
    elif present_count >= 2:
        score += 10
        issues.append(f"Multiple key sections missing ({present_count} of 4 present)")
    else:
        issues.append("Most key sections are missing")

    details["key_sections_present"] = present_count

    has_content = present_count > 0

    balance_score = section_balance.get("balance_score", 0)
    if balance_score >= 80:
        score += 20
        strengths.append("Well-balanced content distribution across sections")
    elif balance_score >= 50:
        score += 10
    elif has_content:
        issues.append("Content is heavily imbalanced — one section dominates")

    details["balance_score"] = balance_score

    has_deviation, order_issues = _check_section_ordering(resume)
    if present_count >= 2 and not has_deviation:
        score += 15
        strengths.append("Sections follow conventional ATS-friendly order")
    elif has_content and has_deviation:
        issues.extend(order_issues[:2])

    details["section_ordering_issues"] = order_issues

    section_length_issues = ats_format.get("section_length_issues", 0)
    if section_length_issues == 0:
        score += 15
        strengths.append("All sections meet minimum length requirements")
    elif has_content and section_length_issues <= 2:
        score += 5
    elif has_content:
        issues.append(f"{section_length_issues} entries have insufficient description length")
    details["section_length_issues"] = section_length_issues

    sq = summary_quality or {}
    grade = sq.get("length_grade", "missing")
    if grade == "ideal":
        score += 10
        strengths.append("Summary length is ideal for ATS parsing")
    elif grade in ("short", "long"):
        score += 5
    elif has_content:
        issues.append("Summary is very short or missing")

    details["summary_grade"] = grade

    score = min(score, max_score)
    return score, details, issues, strengths


def _score_keywords(
    keywords: Dict[str, Any],
    skills_list: Any,
) -> Tuple[int, Dict[str, Any], List[str], List[str]]:
    issues: List[str] = []
    strengths: List[str] = []
    score = 0
    max_score = 100
    details: Dict[str, Any] = {}

    matched = keywords.get("matched_keywords", [])
    missing = keywords.get("missing_common_keywords", [])
    density = keywords.get("keyword_density", 0.0)
    total_words = keywords.get("total_words", 0)

    details["matched_count"] = len(matched)
    details["missing_count"] = len(missing)
    details["keyword_density_pct"] = density

    if len(matched) >= 10:
        score += 35
        strengths.append(f"Strong keyword coverage ({len(matched)} of 40 common keywords matched)")
    elif len(matched) >= 5:
        score += 20
    elif len(matched) >= 2:
        score += 10
    elif len(matched) > 0:
        score += 5
    else:
        issues.append("No common tech keywords found in resume")

    top_missing = [k for k in missing[:5] if k not in ("html", "css")]
    if len(top_missing) >= 3 and len(matched) >= 2:
        issues.append(f"Missing common keywords: {', '.join(top_missing[:3])}")
    details["top_missing_keywords"] = top_missing[:5]

    alignment = _compute_skills_keyword_alignment(skills_list, matched)
    details["skills_keyword_alignment_pct"] = alignment
    if alignment >= 75:
        score += 25
        strengths.append(f"Excellent skills-to-keyword alignment ({alignment}%)")
    elif alignment >= 50:
        score += 15
        strengths.append(f"Good skills-to-keyword alignment ({alignment}%)")
    elif alignment >= 25:
        score += 8
    else:
        if skills_list:
            issues.append(f"Low alignment ({alignment}%) between listed skills and keywords found in text")

    if density >= 20:
        score += 25
        strengths.append(f"Keyword density is well-distributed ({density}%)")
    elif density >= 10:
        score += 15
    else:
        issues.append(f"Low keyword density ({density}%) relative to common benchmarks")

    if total_words == 0:
        score = 0
        issues = ["No text content to analyze for keywords"]
        strengths = []

    score = min(score, max_score)
    return score, details, issues, strengths


def _score_action_verbs(
    action_verbs: Any,
    bullet_quality: Dict[str, Any],
    summary_quality: Dict[str, Any],
) -> Tuple[int, Dict[str, Any], List[str], List[str]]:
    issues: List[str] = []
    strengths: List[str] = []
    score = 0
    max_score = 100
    details: Dict[str, Any] = {}

    av = action_verbs or {}
    total_entries = av.get("total_entries", 0)
    with_verbs = av.get("entries_with_verbs", 0)
    all_verbs = av.get("all_verbs", [])
    unique_verb_count = len(all_verbs)

    details["total_experience_entries"] = total_entries
    details["entries_with_verbs"] = with_verbs
    details["unique_verbs_count"] = unique_verb_count

    if total_entries == 0:
        details["verb_usage_pct"] = 0.0
        score += 20 if summary_quality and summary_quality.get("has_action_verbs") else 0
        if not (summary_quality and summary_quality.get("has_action_verbs")):
            issues.append("No experience entries and summary lacks action verbs")
        score = min(score, max_score)
        return score, details, issues, strengths

    verb_ratio = round((with_verbs / total_entries) * 100, 1)
    details["verb_usage_pct"] = verb_ratio

    if verb_ratio >= 80:
        score += 35
        strengths.append(f"Strong action verb usage ({with_verbs}/{total_entries} entries)")
    elif verb_ratio >= 50:
        score += 20
    elif verb_ratio >= 25:
        score += 10
    else:
        issues.append(f"Low action verb usage ({with_verbs}/{total_entries} entries)")

    if unique_verb_count >= 5:
        score += 25
        strengths.append(f"Good action verb variety ({unique_verb_count} unique verbs)")
    elif unique_verb_count >= 3:
        score += 15
    elif unique_verb_count >= 1:
        score += 5
    else:
        issues.append("No action verbs detected in experience descriptions")

    bq = bullet_quality or {}
    bullet_verb_ratio = bq.get("verb_ratio", 0.0)
    details["bullet_verb_ratio"] = bullet_verb_ratio
    if bullet_verb_ratio >= 60:
        score += 20
        strengths.append(f"{bullet_verb_ratio}% of bullet points start with strong action verbs")
    elif bullet_verb_ratio >= 30:
        score += 10
    else:
        issues.append(f"Only {bullet_verb_ratio}% of bullet points start with action verbs")

    sq = summary_quality or {}
    if sq.get("has_action_verbs"):
        score += 20
        strengths.append("Summary uses action verbs to describe impact")
    else:
        issues.append("Summary lacks action verbs")

    score = min(score, max_score)
    return score, details, issues, strengths


def _score_quantified_impact(
    metrics: Dict[str, Any],
    bullet_quality: Dict[str, Any],
    summary_quality: Dict[str, Any],
    experience: List[Dict],
) -> Tuple[int, Dict[str, Any], List[str], List[str]]:
    issues: List[str] = []
    strengths: List[str] = []
    score = 0
    max_score = 100
    details: Dict[str, Any] = {}

    total_metrics = metrics.get("total_quantifiable", 0)
    percentages = metrics.get("percentages", [])
    currencies = metrics.get("currency_values", [])
    time_metrics = metrics.get("time_metrics", [])
    magnitude_words = metrics.get("magnitude_words", [])

    details["total_metrics"] = total_metrics
    details["percentages_found"] = len(percentages)
    details["currency_found"] = len(currencies)
    details["time_metrics_found"] = len(time_metrics)
    details["magnitude_words_found"] = len(magnitude_words)

    if total_metrics >= 5:
        score += 35
        strengths.append(f"Strong quantifiable achievement metrics ({total_metrics} found)")
    elif total_metrics >= 3:
        score += 20
    elif total_metrics >= 1:
        score += 10
    else:
        issues.append("No quantifiable achievements found (%, $, time metrics)")

    has_percentages = len(percentages) > 0
    has_currencies = len(currencies) > 0
    has_time = len(time_metrics) > 0
    types_present = sum([has_percentages, has_currencies, has_time])
    if types_present >= 2:
        score += 20
        strengths.append("Multiple metric types used (percentages, currency, time)")
    elif types_present == 1:
        score += 10
    else:
        issues.append("No percentage, currency, or time metrics detected")

    details["metric_types_present"] = types_present

    quantified_ratio = _compute_quantified_ratio(metrics, bullet_quality)
    details["quantified_achievement_ratio"] = quantified_ratio
    if quantified_ratio >= 50:
        score += 20
        strengths.append(f"{quantified_ratio}% of bullet points contain quantified achievements")
    elif quantified_ratio >= 25:
        score += 10
        strengths.append(f"{quantified_ratio}% of bullet points contain quantified achievements")
    elif quantified_ratio > 0:
        score += 5
    else:
        issues.append("No quantified achievements in any bullet point")

    mag_count = len(magnitude_words)
    if mag_count >= 5:
        score += 15
        strengths.append(f"Strong impact language ({mag_count} magnitude words)")
    elif mag_count >= 2:
        score += 8
    else:
        issues.append("Weak impact language — few magnitude words detected")

    details["magnitude_word_count"] = mag_count

    sq = summary_quality or {}
    if sq.get("has_metrics"):
        score += 10
        strengths.append("Summary includes quantifiable achievements")
    else:
        issues.append("Summary lacks quantified achievements")

    score = min(score, max_score)
    return score, details, issues, strengths


def _score_contact_info(
    completeness: Dict[str, Any],
    ats_format: Dict[str, Any],
) -> Tuple[int, Dict[str, Any], List[str], List[str]]:
    issues: List[str] = []
    strengths: List[str] = []
    score = 0
    max_score = 100
    details: Dict[str, Any] = {}

    contact = completeness.get("contact", {})
    ats_personal = ats_format.get("personal_info", {})

    has_name = contact.get("has_name") or ats_personal.get("has_name", False)
    has_email = contact.get("has_email") or ats_personal.get("has_email", False)
    has_phone = contact.get("has_phone") or ats_personal.get("has_phone", False)
    has_location = contact.get("has_location") or ats_personal.get("has_location", False)

    details["has_name"] = has_name
    details["has_email"] = has_email
    details["has_phone"] = has_phone
    details["has_location"] = has_location

    ats_critical = sum([has_name, has_email, has_phone])
    if ats_critical >= 3:
        score += 40
        strengths.append("All ATS-critical fields (name, email, phone) are present")
    elif ats_critical == 2:
        score += 20
        missing = []
        if not has_name:
            missing.append("name")
        if not has_email:
            missing.append("email")
        if not has_phone:
            missing.append("phone")
        issues.append(f"Missing ATS-critical field: {', '.join(missing)}")
    else:
        missing = []
        if not has_name:
            missing.append("name")
        if not has_email:
            missing.append("email")
        if not has_phone:
            missing.append("phone")
        issues.append(f"Missing critical ATS fields: {', '.join(missing)}")

    if has_location:
        score += 15
        strengths.append("Location information provided (important for local job searches)")
    else:
        issues.append("Location is missing (helps ATS filter by region)")
    details["has_location"] = has_location

    has_linkedin = contact.get("has_linkedin", False)
    has_github = contact.get("has_github", False)
    has_website = contact.get("has_website", False)
    profile_count = sum([has_linkedin, has_github, has_website])

    details["profile_count"] = profile_count
    if profile_count >= 2:
        score += 25
        strengths.append(f"Strong online professional presence ({profile_count} profiles)")
    elif profile_count == 1:
        score += 15
    else:
        issues.append("No professional profiles (LinkedIn/GitHub/website) — reduces credibility")
    details["has_linkedin"] = has_linkedin
    details["has_github"] = has_github
    details["has_website"] = has_website

    contact_score = contact.get("score", 0)
    if contact_score >= 80:
        score += 20
        strengths.append("Complete contact information section")
    elif contact_score >= 50:
        score += 10

    score = min(score, max_score)
    return score, details, issues, strengths


def _assess_risk(overall_score: int, component_scores: Dict[str, int], findings: Dict[str, Any]) -> Tuple[str, List[str]]:
    if overall_score >= 70:
        risk_level = "low"
    elif overall_score >= 40:
        risk_level = "medium"
    else:
        risk_level = "high"

    risk_factors = []
    for component, score in component_scores.items():
        if score < 30:
            risk_factors.append(f"{component.replace('_', ' ').title()}: very low score ({score}/100)")

    if findings.get("missing_ats_fields"):
        risk_factors.append(f"Missing ATS-critical fields: {', '.join(findings['missing_ats_fields'])}")

    if findings.get("no_metrics"):
        risk_factors.append("No quantifiable achievements — ATS keyword scoring penalizes this")

    if findings.get("section_ordering_deviation"):
        risk_factors.append("Unconventional section ordering may confuse ATS parsers")

    risk_factors = risk_factors[:5]
    return risk_level, risk_factors


def _generate_recommendations(
    component_scores: Dict[str, int],
    findings: Dict[str, Any],
) -> List[str]:
    recs = []

    if component_scores.get("contact_info", 100) < 60:
        recs.append("Add complete contact info: name, email, phone, and location")
    if component_scores.get("contact_info", 100) < 80:
        recs.append("Include LinkedIn and GitHub profile URLs")
    if component_scores.get("structure", 100) < 60:
        recs.append("Ensure all key sections (Summary, Experience, Education, Skills) are present")
    if component_scores.get("structure", 100) < 50:
        recs.append("Reformat resume sections to follow a conventional ATS-friendly order (Summary → Experience → Education → Skills)")
    if component_scores.get("keywords", 100) < 50:
        top_missing = findings.get("top_missing_keywords", [])
        if top_missing:
            recs.append(f"Incorporate industry keywords: {', '.join(top_missing[:5])}")
        else:
            recs.append("Increase keyword density by incorporating relevant industry terms")
    if component_scores.get("action_verbs", 100) < 50:
        recs.append("Start bullet points with strong action verbs (Led, Developed, Implemented, Optimized)")
    if component_scores.get("quantified_impact", 100) < 50:
        recs.append("Add quantified achievements (%, $, time saved) to at least 50% of bullet points")
    if findings.get("date_inconsistency"):
        recs.append("Use a consistent date format throughout (e.g., YYYY-MM)")

    return recs[:6]


def analyze_ats(
    resume: Dict[str, Any],
    completeness: Dict[str, Any],
    action_verbs: Any,
    metrics: Dict[str, Any],
    ats_format: Dict[str, Any],
    keywords: Dict[str, Any],
    bullet_quality: Dict[str, Any],
    section_balance: Dict[str, Any],
    summary_quality: Dict[str, Any],
) -> Dict[str, Any]:
    experience_raw = resume.get("experience") or []
    if not isinstance(experience_raw, list):
        experience_raw = []
    projects_raw = resume.get("projects") or []
    if not isinstance(projects_raw, list):
        projects_raw = []
    skills_raw = resume.get("skills") or []
    if not isinstance(skills_raw, list):
        skills_raw = []

    date_consistency_result, date_issues = _compute_date_consistency(resume)
    bullet_consistency_val, bullet_consistency_grade = _compute_bullet_consistency(experience_raw, projects_raw)

    struct_score, struct_details, struct_issues, struct_strengths = _score_structure(
        resume, completeness, ats_format, section_balance, summary_quality
    )
    kw_score, kw_details, kw_issues, kw_strengths = _score_keywords(keywords, skills_raw)
    av_score, av_details, av_issues, av_strengths = _score_action_verbs(action_verbs, bullet_quality, summary_quality)
    qi_score, qi_details, qi_issues, qi_strengths = _score_quantified_impact(metrics, bullet_quality, summary_quality, experience_raw)
    ci_score, ci_details, ci_issues, ci_strengths = _score_contact_info(completeness, ats_format)

    component_scores = {
        "structure": struct_score,
        "keywords": kw_score,
        "action_verbs": av_score,
        "quantified_impact": qi_score,
        "contact_info": ci_score,
    }

    overall_score = int(
        struct_score * _STRUCTURE_WEIGHT
        + kw_score * _KEYWORDS_WEIGHT
        + av_score * _ACTION_VERBS_WEIGHT
        + qi_score * _QUANTIFIED_WEIGHT
        + ci_score * _CONTACT_WEIGHT
    )
    overall_score = max(0, min(100, overall_score))

    ats_personal = ats_format.get("personal_info", {})
    missing_ats = ats_personal.get("missing_fields", [])

    findings = {
        "missing_ats_fields": missing_ats,
        "no_metrics": qi_details.get("total_metrics", 0) == 0,
        "section_ordering_deviation": len(struct_details.get("section_ordering_issues", [])) > 0,
        "date_format": date_consistency_result,
        "date_inconsistency": len(date_issues) > 0,
        "top_missing_keywords": kw_details.get("top_missing_keywords", []),
        "bullet_consistency_grade": bullet_consistency_grade,
    }

    risk_level, risk_factors = _assess_risk(overall_score, component_scores, findings)

    recommendations = _generate_recommendations(component_scores, findings)

    all_issues = struct_issues + kw_issues + av_issues + qi_issues + ci_issues
    all_warnings = date_issues[:3]
    all_strengths = struct_strengths + kw_strengths + av_strengths + qi_strengths + ci_strengths

    if bullet_consistency_grade == "inconsistent":
        all_warnings.append("Bullet point lengths vary significantly — ATS may have difficulty parsing")
    elif bullet_consistency_grade == "consistent":
        all_strengths.append("Bullet point lengths are consistent across entries")

    return {
        "overall_ats_score": overall_score,
        "component_scores": component_scores,
        "component_details": {
            "structure": {
                "score": struct_score,
                "max_score": 100,
                "issues": struct_issues,
                "strengths": struct_strengths,
                "details": struct_details,
            },
            "keywords": {
                "score": kw_score,
                "max_score": 100,
                "issues": kw_issues,
                "strengths": kw_strengths,
                "details": kw_details,
            },
            "action_verbs": {
                "score": av_score,
                "max_score": 100,
                "issues": av_issues,
                "strengths": av_strengths,
                "details": av_details,
            },
            "quantified_impact": {
                "score": qi_score,
                "max_score": 100,
                "issues": qi_issues,
                "strengths": qi_strengths,
                "details": qi_details,
            },
            "contact_info": {
                "score": ci_score,
                "max_score": 100,
                "issues": ci_issues,
                "strengths": ci_strengths,
                "details": ci_details,
            },
        },
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "recommendations": recommendations,
        "ats_issues": [{"type": "issue", "section": "ats_analysis", "message": m} for m in all_issues],
        "ats_warnings": [{"type": "warning", "section": "ats_analysis", "message": m} for m in all_warnings],
        "ats_strengths": [{"type": "strength", "section": "ats_analysis", "message": m} for m in all_strengths],
        "date_format_consistency": {
            "dominant_format": date_consistency_result,
            "issues": date_issues,
        },
        "bullet_consistency": {
            "std_dev": bullet_consistency_val,
            "grade": bullet_consistency_grade,
        },
    }
