"""Actionable Recommendation Generator — turns analysis results into fixable items.

Maps every issue, warning, weakness, and ATS finding to an actionable
recommendation with:
- Priority (high/medium/low)
- Category (wizard section name)
- Description + evidence
- Recommended fix text
- Navigation target URL (/resume-studio?id=X&section=Y)
"""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_QUALITY_TO_WIZARD: Dict[str, Optional[str]] = {
    "personal": "personal",
    "summary": "summary",
    "experience": "experience",
    "education": "education",
    "skills": "skills",
    "projects": "projects",
    "certifications": "certifications",
    "languages": "languages",
    "interests": "interests",
    "references": "references",
    "resume_length": None,
    "section_balance": None,
    "ats_format": "personal",
}

_ATS_COMPONENT_TO_WIZARD: Dict[str, Optional[str]] = {
    "contact_info": "personal",
    "action_verbs": "experience",
    "quantified_impact": "experience",
    "keywords": "skills",
    "structure": None,
}

_SW_CATEGORY_TO_WIZARD: Dict[str, Optional[str]] = {
    "contact": "personal",
    "summary": "summary",
    "experience": "experience",
    "education": "education",
    "skills": "skills",
    "projects": "projects",
    "certifications": "certifications",
    "ats": "personal",
    "formatting": None,
    "content": None,
}

_WIZARD_INDEX: Dict[str, int] = {
    "personal": 0,
    "summary": 1,
    "experience": 2,
    "education": 3,
    "skills": 4,
    "projects": 5,
    "certifications": 6,
    "languages": 7,
    "interests": 8,
    "references": 9,
}

_PRIORITY_MAP: Dict[str, str] = {
    "high": "high",
    "medium": "medium",
    "low": "low",
}

_FIX_TEMPLATES: Dict[str, str] = {
    "contact": "Update your {section} information in the Personal Information section. {detail}",
    "summary": "Improve your professional summary in the Summary section. {detail}",
    "experience": "Update your {section} entries in the Experience section. {detail}",
    "education": "Complete your {section} details in the Education section. {detail}",
    "skills": "Update your {section} in the Skills section. {detail}",
    "projects": "Fill in your {section} details in the Projects section. {detail}",
    "certifications": "Complete your {section} information in the Certifications section. {detail}",
    "languages": "Review your {section} in the Languages section. {detail}",
    "interests": "Update your {section} in the Interests section. {detail}",
    "references": "Complete your {section} in the References section. {detail}",
    "content": "Review your overall resume content. {detail}",
    "formatting": "Review your resume formatting. {detail}",
    "ats": "Improve your ATS compatibility. {detail}",
}

_DEFAULT_FIX = "Review and improve this section in the Resume Studio."
_EVIDENCE_PREFIX = "Analysis found: "


def _make_nav_url(resume_id: Optional[int], section: Optional[str]) -> Optional[str]:
    """Build navigation URL for the frontend."""
    if resume_id is None:
        return None
    url = f"/resume-studio?id={resume_id}"
    if section:
        url += f"&section={section}"
    return url


def _severity_to_priority(severity: str) -> str:
    return _PRIORITY_MAP.get(severity, "medium")


def _build_fix_text(category: str, section: Optional[str], detail: str) -> str:
    template = _FIX_TEMPLATES.get(category, _DEFAULT_FIX)
    return template.format(section=section or "resume", detail=detail)


def _make_recommendation(
    rec_id: str,
    priority: str,
    category: str,
    description: str,
    evidence: str,
    recommended_fix: str,
    target_section: Optional[str],
    source_type: str,
    resume_id: Optional[int] = None,
    source_id: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "id": rec_id,
        "priority": priority,
        "category": category,
        "description": description,
        "evidence": evidence,
        "recommended_fix": recommended_fix,
        "target_section": target_section,
        "navigation_url": _make_nav_url(resume_id, target_section),
        "source_type": source_type,
        "source_id": source_id,
    }


def _generate_from_quality_report(
    quality_report: Dict[str, Any],
    resume_id: Optional[int],
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if not quality_report:
        return results

    idx = 0
    for finding_type in ("issues", "warnings"):
        findings = quality_report.get(finding_type) or []
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            section = finding.get("section", "")
            message = finding.get("message", "")
            target = _QUALITY_TO_WIZARD.get(section, None)
            priority = "high" if finding_type == "issues" else "medium"
            detail = f"Consider addressing: {message}"
            results.append(_make_recommendation(
                rec_id=f"qr-{finding_type}-{idx}",
                priority=priority,
                category=target or "content",
                description=message,
                evidence=f"{_EVIDENCE_PREFIX}{finding_type.replace('_', ' ')} in {section}",
                recommended_fix=_build_fix_text(
                    target or "content", target or section, detail
                ),
                target_section=target,
                source_type=f"quality_{finding_type[:-1]}",
                resume_id=resume_id,
            ))
            idx += 1

    return results


def _generate_from_strengths_weaknesses(
    sw_result: Dict[str, Any],
    resume_id: Optional[int],
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if not sw_result:
        return results

    idx = 0
    weaknesses = sw_result.get("weaknesses") or []
    for w in weaknesses:
        if not isinstance(w, dict):
            continue
        category = w.get("category", "")
        title = w.get("title", "")
        description = w.get("description", "")
        severity = w.get("severity", "medium")
        target = _SW_CATEGORY_TO_WIZARD.get(category, None)
        priority = _severity_to_priority(severity)

        evidence_text = description or title
        detail = f"Address this {category} weakness."
        results.append(_make_recommendation(
            rec_id=f"sw-{idx}",
            priority=priority,
            category=target or category,
            description=title,
            evidence=f"{_EVIDENCE_PREFIX}{evidence_text}",
            recommended_fix=_build_fix_text(
                category, target or category, detail
            ),
            target_section=target,
            source_type="strength_weakness",
            resume_id=resume_id,
        ))
        idx += 1

    return results


def _generate_from_ats(
    ats_result: Dict[str, Any],
    resume_id: Optional[int],
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if not ats_result:
        return results

    idx = 0
    for issue in (ats_result.get("ats_issues") or []):
        if not isinstance(issue, dict):
            continue
        section = issue.get("section", "")
        message = issue.get("message", "") or issue.get("detail", "")
        target = _QUALITY_TO_WIZARD.get(section, None)
        detail = f"ATS compatibility issue: {message}"
        results.append(_make_recommendation(
            rec_id=f"ats-issue-{idx}",
            priority="high",
            category=target or "ats",
            description=message or "ATS compatibility issue detected",
            evidence=f"{_EVIDENCE_PREFIX}ATS issue in {section or 'resume'}",
            recommended_fix=_build_fix_text(
                "ats", target or section, detail
            ),
            target_section=target,
            source_type="ats_issue",
            resume_id=resume_id,
        ))
        idx += 1

    component_details = ats_result.get("component_details") or {}
    for comp_key, comp in component_details.items():
        if not isinstance(comp, dict):
            continue
        comp_issues = comp.get("issues") or []
        for ci in comp_issues:
            target = _ATS_COMPONENT_TO_WIZARD.get(comp_key, None)
            detail = f"Improve {comp_key.replace('_', ' ')} component."
            results.append(_make_recommendation(
                rec_id=f"ats-comp-{comp_key}-{idx}",
                priority="medium",
                category=target or "ats",
                description=str(ci),
                evidence=f"{_EVIDENCE_PREFIX}{comp_key}: {ci}",
                recommended_fix=_build_fix_text(
                    "ats", target or comp_key, detail
                ),
                target_section=target,
                source_type="ats_issue",
                resume_id=resume_id,
            ))
            idx += 1

    return results


def _generate_from_deep_analysis(
    deep_result: Dict[str, Any],
    resume_id: Optional[int],
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if not deep_result or deep_result.get("status") != "success":
        return results

    ai = deep_result.get("ai_analysis")
    if not ai:
        return results

    idx = 0
    for rec in (ai.get("recommendations") or []):
        if not isinstance(rec, dict):
            continue
        action = rec.get("action", "")
        details = rec.get("details", "")
        priority = "medium"
        category = rec.get("category", "general")
        target_section_map = {
            "summary": "summary",
            "experience": "experience",
            "skills": "skills",
            "projects": "projects",
            "general": None,
        }
        target = target_section_map.get(category, None)
        results.append(_make_recommendation(
            rec_id=f"deep-rec-{idx}",
            priority=priority,
            category=target or "content",
            description=action or "AI recommendation",
            evidence=f"AI analysis: {details}" if details else "AI analysis recommendation",
            recommended_fix=_build_fix_text(
                target or "content", target or category, action or ""
            ),
            target_section=target,
            source_type="deep_analysis",
            resume_id=resume_id,
        ))
        idx += 1

    weaknesses = ai.get("weaknesses") or []
    for w in weaknesses:
        if not isinstance(w, dict):
            continue
        target = _SW_CATEGORY_TO_WIZARD.get(w.get("category", ""), None)
        results.append(_make_recommendation(
            rec_id=f"deep-weakness-{idx}",
            priority="medium",
            category=target or "content",
            description=w.get("title", "AI-identified weakness"),
            evidence=f"AI analysis: {w.get('description', '')}",
            recommended_fix=_build_fix_text(
                target or "content", target or "", w.get("suggestion", "")
            ),
            target_section=target,
            source_type="deep_analysis",
            resume_id=resume_id,
        ))
        idx += 1

    return results


def generate_recommendations(
    analysis_result: Dict[str, Any],
    resume_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Transform a full analysis result into actionable recommendations.

    Args:
        analysis_result: The full output from analysis_service.analyze_resume()
        resume_id: Resume ID for building navigation URLs

    Returns:
        RecommendationsResponse-compatible dict
    """
    all_recs: List[Dict[str, Any]] = []

    quality = analysis_result.get("quality_report")
    sw = analysis_result.get("strengths_weaknesses")
    ats = analysis_result.get("ats_analysis")
    deep = analysis_result.get("deep_analysis")

    all_recs.extend(_generate_from_quality_report(quality, resume_id))
    all_recs.extend(_generate_from_strengths_weaknesses(sw, resume_id))
    all_recs.extend(_generate_from_ats(ats, resume_id))
    all_recs.extend(_generate_from_deep_analysis(deep, resume_id))

    sorted_recs = sorted(
        all_recs,
        key=lambda r: (
            0 if r["priority"] == "high" else
            1 if r["priority"] == "medium" else 2
        ),
    )

    high_count = sum(1 for r in sorted_recs if r["priority"] == "high")

    logger.info(
        "Generated %d recommendations (%d high priority)",
        len(sorted_recs), high_count,
    )

    return {
        "recommendations": sorted_recs,
        "total_count": len(sorted_recs),
        "high_priority_count": high_count,
    }
