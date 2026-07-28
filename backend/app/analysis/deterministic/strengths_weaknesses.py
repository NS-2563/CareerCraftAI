"""Deterministic Strengths & Weaknesses Analysis.

Evaluates all existing analysis signals against thresholds to produce
structured, evidence-backed strengths and weaknesses.

Every finding references an actual analysis signal via the `evidence` field.
Architecture designed so Phase 3G can add AI-powered contextual findings
(by appending to the results with source="ai") without replacing deterministic ones.
"""
from typing import Any, Dict, List, Optional


_SOURCE = "deterministic"


def _strength(
    category: str,
    title: str,
    description: str,
    severity: str,
    evidence: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "type": "strength",
        "category": category,
        "title": title,
        "description": description,
        "severity": severity,
        "evidence": evidence,
        "source": _SOURCE,
    }


def _weakness(
    category: str,
    title: str,
    description: str,
    severity: str,
    priority: str,
    evidence: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "type": "weakness",
        "category": category,
        "title": title,
        "description": description,
        "severity": severity,
        "priority": priority,
        "evidence": evidence,
        "source": _SOURCE,
    }


def _check_contact(
    completeness: Dict[str, Any],
) -> List[Dict[str, Any]]:
    findings = []
    contact = completeness.get("contact", {})

    fields_present = contact.get("fields_present", 0)
    has_name = contact.get("has_name", False)
    has_email = contact.get("has_email", False)
    has_phone = contact.get("has_phone", False)
    has_location = contact.get("has_location", False)
    has_linkedin = contact.get("has_linkedin", False)
    has_github = contact.get("has_github", False)
    has_website = contact.get("has_website", False)

    if has_name and has_email and has_phone:
        findings.append(_strength(
            category="contact",
            title="Complete Contact Information",
            description=f"Resume includes name, email, and phone ({fields_present}/3 critical fields).",
            severity="high",
            evidence={"fields_present": fields_present, "has_name": has_name, "has_email": has_email, "has_phone": has_phone},
        ))

    if has_location:
        findings.append(_strength(
            category="contact",
            title="Location Provided",
            description="Resume includes location, which helps with geographic targeting.",
            severity="medium",
            evidence={"has_location": has_location},
        ))

    if has_linkedin or has_github or has_website:
        profiles = sum([has_linkedin, has_github, has_website])
        findings.append(_strength(
            category="contact",
            title="Professional Profiles Present",
            description=f"Resume includes {profiles} professional profile(s).",
            severity="medium",
            evidence={"has_linkedin": has_linkedin, "has_github": has_github, "has_website": has_website},
        ))

    missing_fields = []
    if not has_name:
        missing_fields.append("name")
    if not has_email:
        missing_fields.append("email")
    if not has_phone:
        missing_fields.append("phone")

    if missing_fields:
        findings.append(_weakness(
            category="contact",
            title="Missing Contact Information",
            description=f"Missing field(s): {', '.join(missing_fields)}. Recruiters cannot reach you without complete contact info.",
            severity="high",
            priority="high",
            evidence={"missing_fields": missing_fields, "fields_present": fields_present},
        ))

    return findings


def _check_summary(
    summary_quality: Dict[str, Any],
) -> List[Dict[str, Any]]:
    findings = []
    present = summary_quality.get("present", False)
    score = summary_quality.get("summary_quality_score", 0)
    length_grade = summary_quality.get("length_grade", "missing")
    word_count = summary_quality.get("word_count", 0)
    has_verbs = summary_quality.get("has_action_verbs", False)
    has_metrics = summary_quality.get("has_metrics", False)
    keyword_count = summary_quality.get("keyword_count", 0)

    if not present:
        findings.append(_weakness(
            category="summary",
            title="Missing Professional Summary",
            description="No summary section found. A well-crafted summary helps recruiters quickly understand your profile.",
            severity="high",
            priority="high",
            evidence={"present": present, "word_count": word_count},
        ))
        return findings

    if score >= 70:
        findings.append(_strength(
            category="summary",
            title="Strong Professional Summary",
            description=f"Summary quality score is {score}/100 with {word_count} words.",
            severity="high",
            evidence={"summary_quality_score": score, "word_count": word_count},
        ))

    if length_grade == "ideal":
        findings.append(_strength(
            category="summary",
            title="Well-Paced Summary Length",
            description=f"Summary is {word_count} words, within the ideal 30-100 word range.",
            severity="medium",
            evidence={"word_count": word_count, "length_grade": length_grade},
        ))

    if length_grade == "very_short":
        findings.append(_weakness(
            category="summary",
            title="Summary Too Short",
            description=f"Summary is only {word_count} word(s). Aim for 30-100 words to effectively summarize qualifications.",
            severity="medium",
            priority="medium",
            evidence={"word_count": word_count, "length_grade": length_grade},
        ))

    if length_grade == "long":
        findings.append(_weakness(
            category="summary",
            title="Summary May Be Too Long",
            description=f"Summary is {word_count} words. Consider condensing to under 100 words for maximum impact.",
            severity="low",
            priority="low",
            evidence={"word_count": word_count, "length_grade": length_grade},
        ))

    if not has_verbs:
        findings.append(_weakness(
            category="summary",
            title="No Action Verbs in Summary",
            description="Summary lacks action verbs. Using action verbs like 'led', 'developed', 'designed' adds impact.",
            severity="medium",
            priority="medium",
            evidence={"has_action_verbs": has_verbs},
        ))

    if not has_metrics:
        findings.append(_weakness(
            category="summary",
            title="No Quantified Metrics in Summary",
            description="Summary has no quantified achievements. Numbers and metrics make summaries more compelling.",
            severity="low",
            priority="low",
            evidence={"has_metrics": has_metrics},
        ))

    if keyword_count >= 3:
        findings.append(_strength(
            category="summary",
            title="Keyword-Rich Summary",
            description=f"Summary contains {keyword_count} relevant industry keywords.",
            severity="medium",
            evidence={"keyword_count": keyword_count, "keywords_found": summary_quality.get("keywords_found", [])},
        ))

    return findings


def _check_experience(
    completeness: Dict[str, Any],
    action_verbs: Optional[Dict[str, Any]],
    metrics: Dict[str, Any],
    bullet_quality: Dict[str, Any],
) -> List[Dict[str, Any]]:
    findings = []
    exp_comp = completeness.get("section_completeness", {}).get("experience", {})
    exp_present = completeness.get("section_presence", {}).get("experience", False)

    if not exp_present:
        findings.append(_weakness(
            category="experience",
            title="No Work Experience Section",
            description="Resume has no experience section. Work history is critical for most roles.",
            severity="high",
            priority="high",
            evidence={"section_present": exp_present},
        ))
        return findings

    exp_score = exp_comp.get("score", 0)
    if exp_score >= 80:
        findings.append(_strength(
            category="experience",
            title="Complete Experience Entries",
            description=f"Experience entries score {exp_score}/100 for completeness.",
            severity="high",
            evidence={"completeness_score": exp_score, "entry_count": exp_comp.get("entry_count", 0)},
        ))
    elif exp_score < 60:
        findings.append(_weakness(
            category="experience",
            title="Incomplete Experience Entries",
            description=f"Experience entries score only {exp_score}/100. Some entries are missing company, position, dates, or descriptions.",
            severity="high",
            priority="high",
            evidence={"completeness_score": exp_score, "entry_count": exp_comp.get("entry_count", 0)},
        ))
    elif exp_score < 80:
        findings.append(_weakness(
            category="experience",
            title="Partially Complete Experience Entries",
            description=f"Experience entries score {exp_score}/100. Review entries for missing fields.",
            severity="medium",
            priority="medium",
            evidence={"completeness_score": exp_score, "entry_count": exp_comp.get("entry_count", 0)},
        ))

    if action_verbs:
        total = action_verbs.get("total_entries", 0)
        with_verbs = action_verbs.get("entries_with_verbs", 0)
        if total > 0 and with_verbs == total:
            findings.append(_strength(
                category="experience",
                title="Strong Action Verb Usage",
                description=f"All {total} experience entr{'y' if total == 1 else 'ies'} contain{'s' if total == 1 else ''} action verbs.",
                severity="high",
                evidence={"total_entries": total, "entries_with_verbs": with_verbs},
            ))
        elif total > 0 and with_verbs / total >= 0.8:
            findings.append(_strength(
                category="experience",
                title="High Action Verb Coverage",
                description=f"{with_verbs}/{total} experience entries use action verbs ({round(with_verbs/total*100)}%).",
                severity="medium",
                evidence={"total_entries": total, "entries_with_verbs": with_verbs, "verb_ratio": round(with_verbs/total*100)},
            ))
        elif total > 0 and with_verbs / total < 0.5:
            findings.append(_weakness(
                category="experience",
                title="Weak Action Verb Usage",
                description=f"Only {with_verbs}/{total} experience entries use action verbs ({round(with_verbs/total*100)}%). Start bullet points with strong verbs.",
                severity="high",
                priority="high",
                evidence={"total_entries": total, "entries_with_verbs": with_verbs, "verb_ratio": round(with_verbs/total*100)},
            ))

    bullet_score = bullet_quality.get("bullet_quality_score", 0)
    if bullet_score >= 70:
        findings.append(_strength(
            category="experience",
            title="Good Bullet Quality",
            description=f"Bullet quality score is {bullet_score}/100 with {bullet_quality.get('total_bullets', 0)} bullet points.",
            severity="medium",
            evidence={"bullet_quality_score": bullet_score, "total_bullets": bullet_quality.get("total_bullets", 0)},
        ))
    elif bullet_score < 40 and bullet_quality.get("total_bullets", 0) > 0:
        findings.append(_weakness(
            category="experience",
            title="Poor Bullet Quality",
            description=f"Bullet quality score is only {bullet_score}/100. Bullets may lack action verbs, proper punctuation, or appropriate length.",
            severity="medium",
            priority="medium",
            evidence={"bullet_quality_score": bullet_score, "verb_ratio": bullet_quality.get("verb_ratio"), "period_ratio": bullet_quality.get("period_ratio")},
        ))

    total_quant = metrics.get("total_quantifiable", 0)
    mag_words = metrics.get("magnitude_words", [])
    total_metrics = total_quant + len(mag_words)

    if total_metrics >= 5:
        findings.append(_strength(
            category="experience",
            title="Strong Quantified Achievements",
            description=f"Found {total_metrics} quantified metrics and magnitude words across experience entries.",
            severity="high",
            evidence={"total_quantifiable": total_quant, "magnitude_words": mag_words, "total_metrics": total_metrics},
        ))
    elif total_metrics >= 3:
        findings.append(_strength(
            category="experience",
            title="Some Quantified Achievements",
            description=f"Found {total_metrics} quantified metrics and magnitude words. Adding more strengthens impact.",
            severity="low",
            evidence={"total_quantifiable": total_quant, "magnitude_words": mag_words, "total_metrics": total_metrics},
        ))
    elif total_metrics == 0:
        findings.append(_weakness(
            category="experience",
            title="No Quantified Achievements",
            description="No percentages, currency values, time metrics, or magnitude words found. Quantified achievements significantly boost resume impact.",
            severity="high",
            priority="high",
            evidence={"total_quantifiable": total_quant, "magnitude_word_count": len(mag_words)},
        ))
    else:
        findings.append(_weakness(
            category="experience",
            title="Few Quantified Achievements",
            description=f"Only {total_metrics} quantified metric(s) found. Aim for at least 3-5 to demonstrate impact.",
            severity="medium",
            priority="medium",
            evidence={"total_quantifiable": total_quant, "magnitude_words": mag_words, "total_metrics": total_metrics},
        ))

    return findings


def _check_projects(
    completeness: Dict[str, Any],
) -> List[Dict[str, Any]]:
    findings = []
    proj_comp = completeness.get("section_completeness", {}).get("projects", {})
    proj_present = completeness.get("section_presence", {}).get("projects", False)

    if not proj_present:
        return findings

    proj_score = proj_comp.get("score", 0)
    entry_count = proj_comp.get("entry_count", 0)

    if proj_score >= 70 and entry_count >= 1:
        findings.append(_strength(
            category="projects",
            title="Good Project Coverage",
            description=f"Projects section scores {proj_score}/100 with {entry_count} entr{'y' if entry_count == 1 else 'ies'}.",
            severity="medium",
            evidence={"completeness_score": proj_score, "entry_count": entry_count},
        ))

    if proj_score < 50:
        desc_missing = 0
        entries = proj_comp.get("entries", [])
        for e in entries:
            if isinstance(e, dict) and not e.get("description"):
                desc_missing += 1
        findings.append(_weakness(
            category="projects",
            title="Missing Project Descriptions",
            description=f"Projects section scores {proj_score}/100. {desc_missing} entr{'y' if desc_missing == 1 else 'ies'} missing {'a' if desc_missing == 1 else ''} description.",
            severity="medium",
            priority="medium",
            evidence={"completeness_score": proj_score, "entry_count": entry_count, "entries_missing_description": desc_missing},
        ))

    return findings


def _check_education(
    completeness: Dict[str, Any],
) -> List[Dict[str, Any]]:
    findings = []
    edu_comp = completeness.get("section_completeness", {}).get("education", {})
    edu_present = completeness.get("section_presence", {}).get("education", False)

    if not edu_present:
        return findings

    edu_score = edu_comp.get("score", 0)
    entry_count = edu_comp.get("entry_count", 0)

    if edu_score >= 80:
        findings.append(_strength(
            category="education",
            title="Complete Education Information",
            description=f"Education entries score {edu_score}/100 with {entry_count} entr{'y' if entry_count == 1 else 'ies'}.",
            severity="high",
            evidence={"completeness_score": edu_score, "entry_count": entry_count},
        ))
    elif edu_score < 60:
        findings.append(_weakness(
            category="education",
            title="Incomplete Education Entries",
            description=f"Education entries score {edu_score}/100. Some entries missing institution, degree, or dates.",
            severity="medium",
            priority="medium",
            evidence={"completeness_score": edu_score, "entry_count": entry_count},
        ))

    return findings


def _check_certifications(
    completeness: Dict[str, Any],
) -> List[Dict[str, Any]]:
    findings = []
    cert_comp = completeness.get("section_completeness", {}).get("certifications", {})
    cert_present = completeness.get("section_presence", {}).get("certifications", False)

    if not cert_present:
        findings.append(_weakness(
            category="certifications",
            title="No Certifications Listed",
            description="No certifications section found. Relevant certifications can differentiate you from other candidates.",
            severity="low",
            priority="low",
            evidence={"section_present": cert_present},
        ))
        return findings

    cert_score = cert_comp.get("score", 0)
    entry_count = cert_comp.get("entry_count", 0)

    if cert_score >= 80:
        findings.append(_strength(
            category="certifications",
            title="Complete Certification Information",
            description=f"Certifications score {cert_score}/100 with {entry_count} entr{'y' if entry_count == 1 else 'ies'}.",
            severity="medium",
            evidence={"completeness_score": cert_score, "entry_count": entry_count},
        ))

    return findings


def _check_skills(
    skill_analysis: Dict[str, Any],
    keywords: Dict[str, Any],
    completeness: Dict[str, Any],
) -> List[Dict[str, Any]]:
    findings = []
    skills_present = completeness.get("section_presence", {}).get("skills", False)

    if not skills_present:
        findings.append(_weakness(
            category="skills",
            title="No Skills Section",
            description="No skills section found. A dedicated skills section helps ATS systems and recruiters quickly assess qualifications.",
            severity="high",
            priority="high",
            evidence={"section_present": skills_present},
        ))
        return findings

    explicit_count = skill_analysis.get("explicit_count", 0)
    skill_count = skill_analysis.get("skill_count", 0)

    if explicit_count >= 8:
        findings.append(_strength(
            category="skills",
            title="Strong Skills Coverage",
            description=f"Resume lists {explicit_count} explicit skills across {len(skill_analysis.get('categorized', {}))} categories.",
            severity="high",
            evidence={"explicit_count": explicit_count, "total_skills": skill_count},
        ))
    elif explicit_count >= 5:
        findings.append(_strength(
            category="skills",
            title="Good Skills Coverage",
            description=f"Resume lists {explicit_count} explicit skills. Consider adding a few more for stronger keyword coverage.",
            severity="low",
            evidence={"explicit_count": explicit_count, "total_skills": skill_count},
        ))
    elif explicit_count < 3:
        findings.append(_weakness(
            category="skills",
            title="Few Skills Listed",
            description=f"Only {explicit_count} explicit skills listed. Aim for at least 5-8 relevant skills.",
            severity="medium",
            priority="medium",
            evidence={"explicit_count": explicit_count, "total_skills": skill_count},
        ))

    keyword_density = keywords.get("keyword_density", 0)
    if keyword_density >= 60:
        findings.append(_strength(
            category="skills",
            title="High Keyword Density",
            description=f"Keyword density is {keyword_density}% — {keywords.get('keyword_count', 0)} of {len(keywords.get('keywords_found', {}))} tracked keywords matched.",
            severity="high",
            evidence={"keyword_density": keyword_density, "keyword_count": keywords.get("keyword_count", 0)},
        ))
    elif keyword_density < 30:
        missing = keywords.get("missing_common_keywords", [])
        findings.append(_weakness(
            category="skills",
            title="Low Keyword Coverage",
            description=f"Keyword density is only {keyword_density}%. {len(missing)} common keywords not found.",
            severity="high",
            priority="high",
            evidence={"keyword_density": keyword_density, "keyword_count": keywords.get("keyword_count", 0), "missing_common_keywords": missing},
        ))

    return findings


def _check_formatting(
    ats_analysis: Dict[str, Any],
    section_balance: Dict[str, Any],
) -> List[Dict[str, Any]]:
    findings = []

    bullet_grade = ats_analysis.get("bullet_consistency", {}).get("grade", "insufficient_data")
    if bullet_grade == "consistent":
        findings.append(_strength(
            category="formatting",
            title="Consistent Bullet Formatting",
            description="Bullet points have consistent punctuation and length, improving readability.",
            severity="medium",
            evidence={"bullet_consistency_grade": bullet_grade},
        ))
    elif bullet_grade == "inconsistent":
        findings.append(_weakness(
            category="formatting",
            title="Inconsistent Bullet Formatting",
            description="Bullet points vary significantly in length and punctuation. Consistent formatting improves professional appearance.",
            severity="low",
            priority="low",
            evidence={"bullet_consistency_grade": bullet_grade},
        ))

    date_issues = ats_analysis.get("date_format_consistency", {}).get("issues", [])
    if date_issues:
        findings.append(_weakness(
            category="formatting",
            title="Inconsistent Date Formats",
            description=f"Date format issue(s): {'; '.join(date_issues)}. Use a single date format throughout.",
            severity="medium",
            priority="medium",
            evidence={"date_issues": date_issues},
        ))

    balance_score = section_balance.get("balance_score", 0)
    if balance_score >= 70:
        findings.append(_strength(
            category="formatting",
            title="Well-Balanced Sections",
            description=f"Section balance score is {balance_score}/100. Content is well-distributed across sections.",
            severity="medium",
            evidence={"balance_score": balance_score, "section_count": section_balance.get("section_count", 0)},
        ))
    elif balance_score < 40:
        dominant = section_balance.get("dominant_section", "unknown")
        findings.append(_weakness(
            category="formatting",
            title="Unbalanced Sections",
            description=f"Section balance score is {balance_score}/100. '{dominant}' section dominates the resume content.",
            severity="medium",
            priority="medium",
            evidence={"balance_score": balance_score, "dominant_section": dominant, "balance_issues": section_balance.get("balance_issues", [])},
        ))

    return findings


def _check_ats(
    ats_analysis: Dict[str, Any],
) -> List[Dict[str, Any]]:
    findings = []
    overall = ats_analysis.get("overall_ats_score", 0)
    risk = ats_analysis.get("risk_level", "high")
    risk_factors = ats_analysis.get("risk_factors", [])
    components = ats_analysis.get("component_scores", {})

    if overall >= 70:
        findings.append(_strength(
            category="ats",
            title="ATS-Ready Resume",
            description=f"Overall ATS score is {overall}/100 with {risk} risk level.",
            severity="high",
            evidence={"overall_ats_score": overall, "risk_level": risk, "component_scores": components},
        ))

    if risk == "high" or risk_factors:
        if risk_factors:
            findings.append(_weakness(
                category="ats",
                title="ATS Compatibility Risks",
                description=f"ATS risk level is '{risk}'. Factors: {'; '.join(risk_factors[:3])}.",
                severity="high" if risk == "high" else "medium",
                priority="high" if risk == "high" else "medium",
                evidence={"risk_level": risk, "risk_factors": risk_factors, "component_scores": components},
            ))

    for comp_name, comp_key in [("Structure", "structure"), ("Keywords", "keywords"),
                                  ("Action Verbs", "action_verbs"), ("Quantified Impact", "quantified_impact"),
                                  ("Contact Info", "contact_info")]:
        comp_score = components.get(comp_key, 0)
        if comp_score >= 80:
            findings.append(_strength(
                category="ats",
                title=f"Strong {comp_name} Component",
                description=f"ATS {comp_name.lower()} score is {comp_score}/100.",
                severity="medium",
                evidence={"component": comp_key, "score": comp_score},
            ))

    return findings


def _check_overall_coverage(
    completeness: Dict[str, Any],
) -> List[Dict[str, Any]]:
    findings = []
    overall_score = completeness.get("overall_completeness_score", 0)
    section_presence = completeness.get("section_presence", {})

    if overall_score >= 80:
        present_count = sum(1 for v in section_presence.values() if v)
        total = len(section_presence)
        findings.append(_strength(
            category="content",
            title="Strong Section Coverage",
            description=f"Completeness score is {overall_score}/100 — {present_count}/{total} sections present.",
            severity="high",
            evidence={"overall_completeness_score": overall_score, "present_sections": present_count, "total_sections": total},
        ))
    elif overall_score < 50:
        findings.append(_weakness(
            category="content",
            title="Poor Section Completeness",
            description=f"Completeness score is only {overall_score}/100. Several key sections may be missing.",
            severity="high",
            priority="high",
            evidence={"overall_completeness_score": overall_score, "section_presence": section_presence},
        ))

    return findings


def _check_resume_length(
    quality_report: Dict[str, Any],
) -> List[Dict[str, Any]]:
    findings = []
    length_info = quality_report.get("resume_length", {})
    grade = length_info.get("grade", "empty")
    total_words = length_info.get("total_words", 0)

    if grade == "ideal":
        findings.append(_strength(
            category="content",
            title="Optimal Resume Length",
            description=f"Resume is {total_words} words, within the ideal 300-700 word range.",
            severity="medium",
            evidence={"total_words": total_words, "grade": grade},
        ))
    elif grade in ("very_short", "short"):
        findings.append(_weakness(
            category="content",
            title="Resume Too Short",
            description=f"Resume is only {total_words} words. Aim for 300-700 words for sufficient depth.",
            severity="medium",
            priority="medium",
            evidence={"total_words": total_words, "grade": grade, "recommendation": length_info.get("recommendation", "")},
        ))
    elif grade == "long":
        findings.append(_weakness(
            category="content",
            title="Resume May Be Too Long",
            description=f"Resume is {total_words} words. Consider trimming to under 700 words.",
            severity="low",
            priority="low",
            evidence={"total_words": total_words, "grade": grade, "recommendation": length_info.get("recommendation", "")},
        ))

    return findings


def analyze_strengths_weaknesses(
    resume: Dict[str, Any],
    completeness: Dict[str, Any],
    action_verbs: Optional[Dict[str, Any]],
    metrics: Dict[str, Any],
    ats_format: Dict[str, Any],
    keywords: Dict[str, Any],
    bullet_quality: Dict[str, Any],
    section_balance: Dict[str, Any],
    summary_quality: Dict[str, Any],
    quality_report: Dict[str, Any],
    ats_analysis: Dict[str, Any],
    skill_analysis: Dict[str, Any],
) -> Dict[str, Any]:
    """Run deterministic strengths & weaknesses analysis.

    Takes all existing analysis outputs and evaluates them against
    thresholds to produce structured, evidence-backed findings.

    Returns:
        Dict with:
            strengths: List[Dict] — structured strength findings
            weaknesses: List[Dict] — structured weakness findings
            strength_count: int
            weakness_count: int
            top_priorities: List[str] — high-priority weakness titles
    """
    findings: List[Dict[str, Any]] = []
    findings.extend(_check_contact(completeness))
    findings.extend(_check_summary(summary_quality))
    findings.extend(_check_experience(completeness, action_verbs, metrics, bullet_quality))
    findings.extend(_check_projects(completeness))
    findings.extend(_check_education(completeness))
    findings.extend(_check_certifications(completeness))
    findings.extend(_check_skills(skill_analysis, keywords, completeness))
    findings.extend(_check_formatting(ats_analysis, section_balance))
    findings.extend(_check_ats(ats_analysis))
    findings.extend(_check_overall_coverage(completeness))
    findings.extend(_check_resume_length(quality_report))

    strengths = [f for f in findings if f["type"] == "strength"]
    weaknesses = [f for f in findings if f["type"] == "weakness"]

    weaknesses_sorted = sorted(
        weaknesses,
        key=lambda w: {"high": 0, "medium": 1, "low": 2}.get(w.get("priority", "low"), 3),
    )
    top_priorities = [w["title"] for w in weaknesses_sorted[:3]]

    return {
        "strengths": strengths,
        "weaknesses": weaknesses_sorted,
        "strength_count": len(strengths),
        "weakness_count": len(weaknesses),
        "top_priorities": top_priorities,
    }
