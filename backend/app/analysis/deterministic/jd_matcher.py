"""Deterministic JD Matcher — reproducible resume-to-job-description matching.

Operates entirely on structured resume data and raw JD text:
1. Extracts technical skills from JD text using the skill catalog
2. Extracts keywords from JD text (significant terms, excluding stop words)
3. Compares JD skills against resume skills (explicit + implicit + cert-derived)
4. Detects partial/normalized matches (e.g., "JS" vs "JavaScript")
5. Computes match scores by category
6. Assesses experience relevance (year requirements, domain overlap)
7. All results are purely deterministic and reproducible
"""
import logging
import re
from typing import Any, Dict, List, Set, Tuple

from app.analysis.deterministic.skill_analysis import analyze_skills
from app.analysis.deterministic.skill_catalog import (
    CATEGORY_LABELS,
    find_category,
    is_known_skill,
    normalize_name,
)

logger = logging.getLogger(__name__)

_STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "need",
    "this", "that", "these", "those", "it", "its", "we", "our", "you",
    "your", "they", "their", "he", "she", "him", "her", "his", "not",
    "no", "nor", "so", "if", "then", "than", "just", "about", "above",
    "after", "again", "all", "also", "any", "because", "been", "before",
    "being", "between", "both", "each", "few", "more", "most", "other",
    "some", "such", "only", "own", "same", "too", "very", "what", "when",
    "where", "which", "who", "whom", "why", "how", "many", "much", "while",
    "yet", "into", "over", "under", "up", "out", "off", "down", "here",
    "there", "every", "both", "must", "per", "via", "year", "years",
    "including", "including:", "etc", "e.g", "i.e", "eg", "ie",
    "work", "working", "experience", "ability", "able", "using",
    "within", "across", "along", "among", "around", "throughout",
    "well", "various", "multiple", "including", "related",
    "minimum", "preferred", "required", "qualifications", "skills",
    "responsibilities", "requirements", "description", "position", "role",
    "candidate", "ideal", "successful", "proven", "track", "record",
    "strong", "demonstrated", "knowledge", "understanding", "familiarity",
    "proficiency", "expertise", "hands-on", "practical", "prior",
}

_JD_MAX_LENGTH = 10000


def _extract_skills_from_jd(jd_text: str) -> List[Dict[str, Any]]:
    """Extract known technical skills from JD text using the skill catalog."""
    if not jd_text or not isinstance(jd_text, str):
        return []

    lower = jd_text.lower()
    found: Dict[str, Dict[str, Any]] = {}

    for _, skills in CATEGORY_LABELS.items():
        pass

    from app.analysis.deterministic.skill_catalog import (
        _ALL_CANONICAL,
        _NORMALIZATION_MAP,
        CATEGORY_INDEX,
    )

    tokens = re.findall(r"[a-zA-Z][a-zA-Z#.+]*", lower)
    multi_word = []
    for i in range(len(tokens)):
        for j in range(i + 1, min(i + 4, len(tokens) + 1)):
            multi_word.append(" ".join(tokens[i:j]))

    candidates = set(tokens + multi_word)

    for candidate in candidates:
        candidate = candidate.strip().rstrip(".")
        if not candidate:
            continue
        if candidate in _ALL_CANONICAL:
            cat = find_category(candidate)
            display = _normalize_skill_name(candidate)
            if candidate not in found:
                found[candidate] = {
                    "name": display,
                    "category": cat,
                    "matched_text": candidate,
                }
        elif candidate in _NORMALIZATION_MAP:
            canonical = _NORMALIZATION_MAP[candidate]
            if canonical.lower() in _ALL_CANONICAL:
                cat = find_category(canonical.lower())
                display = _normalize_skill_name(canonical)
                if display not in found:
                    found[display] = {
                        "name": display,
                        "category": cat,
                        "matched_text": candidate,
                    }

    return list(found.values())


def _normalize_skill_name(name: str) -> str:
    """Get the canonical display name for a skill."""
    from app.analysis.deterministic.skill_catalog import canonical_display_name
    return canonical_display_name(name)


def _extract_keywords(text: str) -> List[str]:
    """Extract significant keywords from text, excluding stop words."""
    if not text or not isinstance(text, str):
        return []

    lower = text.lower()
    tokens = re.findall(r"[a-zA-Z][a-zA-Z#.+]+(?:[-/][a-zA-Z0-9#.+]+)*", lower)

    significant = []
    for token in tokens:
        t = token.strip().rstrip(".").lower()
        if len(t) >= 3 and t not in _STOP_WORDS:
            significant.append(t)

    seen: Set[str] = set()
    unique = []
    for kw in significant:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)

    return unique


def _extract_jd_year_requirement(jd_text: str) -> int:
    """Extract years of experience required from JD text."""
    patterns = [
        r"(\d+)\+?\s*(?:year|yr)s?\s*(?:of\s+)?experience",
        r"experience\s*(?:of\s+)?(\d+)\+?\s*(?:year|yr)s?",
        r"minimum\s*(?:of\s+)?(\d+)\+?\s*(?:year|yr)s?",
    ]
    years = []
    for pattern in patterns:
        matches = re.findall(pattern, jd_text.lower())
        for m in matches:
            try:
                years.append(int(m))
            except ValueError:
                pass
    return max(years) if years else 0


def _calculate_experience_years(resume: Dict[str, Any]) -> Tuple[int, List[str]]:
    """Calculate total years of experience from resume."""
    experience = resume.get("experience") or []
    if not isinstance(experience, list):
        return 0, []

    total_days = 0
    domains: Set[str] = set()
    for exp in experience:
        if not isinstance(exp, dict):
            continue
        start = exp.get("start_date") or exp.get("startDate") or ""
        end = exp.get("end_date") or exp.get("endDate") or ""
        current = exp.get("current") or False
        company = exp.get("company") or ""
        position = exp.get("position") or ""
        if company:
            domains.add(company.lower().strip())
        if position:
            domains.add(position.lower().strip())

        try:
            from datetime import datetime, timezone
            start_dt = None
            if start and len(str(start)) >= 4:
                try:
                    start_dt = datetime.strptime(str(start)[:10], "%Y-%m-%d")
                except ValueError:
                    try:
                        start_dt = datetime.strptime(str(start)[:7], "%Y-%m")
                    except ValueError:
                        try:
                            start_dt = datetime.strptime(str(start)[:4], "%Y")
                        except ValueError:
                            pass

            if current or not end:
                end_dt = datetime.now(timezone.utc).replace(tzinfo=None)
            elif end and len(str(end)) >= 4:
                try:
                    end_dt = datetime.strptime(str(end)[:10], "%Y-%m-%d")
                except ValueError:
                    try:
                        end_dt = datetime.strptime(str(end)[:7], "%Y-%m")
                    except ValueError:
                        try:
                            end_dt = datetime.strptime(str(end)[:4], "%Y")
                        except ValueError:
                            end_dt = None
                if end_dt is None:
                    continue
            else:
                continue

            if start_dt and end_dt and end_dt > start_dt:
                total_days += (end_dt - start_dt).days
        except Exception:
            continue

    total_years = int(round(total_days / 365.25)) if total_days > 0 else 0
    return total_years, list(domains)


def _normalize_resume_for_matching(resume: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize resume data to canonical snake_case format."""
    normalized = dict(resume)

    camel_to_snake = {
        "firstName": "first_name", "lastName": "last_name",
        "startDate": "start_date", "endDate": "end_date",
        "fieldOfStudy": "field_of_study",
    }

    personal = normalized.get("personal") or {}
    if isinstance(personal, dict):
        norm_personal = {}
        for k, v in personal.items():
            norm_personal[camel_to_snake.get(k, k)] = v
        normalized["personal"] = norm_personal

    for section in ("experience", "education", "projects", "certifications"):
        items = normalized.get(section) or []
        if isinstance(items, list):
            norm_items = []
            for item in items:
                if isinstance(item, dict):
                    norm_item = {}
                    for k, v in item.items():
                        norm_item[camel_to_snake.get(k, k)] = v
                    norm_items.append(norm_item)
                else:
                    norm_items.append(item)
            normalized[section] = norm_items

    return normalized


def _get_resume_skills(resume: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get all skills from resume (explicit + implicit + cert-derived) using skill_analysis."""
    try:
        result = analyze_skills(resume)
        return result.get("all_skills", [])
    except Exception as e:
        logger.warning("Skill analysis failed: %s", e)
        return []


def _match_skills(
    resume_skills: List[Dict[str, Any]],
    jd_skills: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Match resume skills against JD skills.

    Returns:
        Tuple of (matched_skills, missing_skills, partial_matches)
    """
    resume_lower: Dict[str, Dict[str, Any]] = {}
    for s in resume_skills:
        name = s.get("name", "")
        if isinstance(name, str) and name.strip():
            resume_lower[name.lower().strip()] = s

    normalized_variants: Dict[str, str] = {}
    for s in resume_skills:
        name = s.get("name", "")
        original = s.get("original_name", "")
        if isinstance(original, str) and original.strip() and original.lower() != name.lower():
            normalized_variants[original.lower().strip()] = name

    matched: List[Dict[str, Any]] = []
    missing: List[Dict[str, Any]] = []
    partial: List[Dict[str, Any]] = []

    for jd_skill in jd_skills:
        jd_name = jd_skill.get("name", "")
        jd_lower = jd_name.lower().strip() if isinstance(jd_name, str) else ""

        if jd_lower in resume_lower:
            matched.append({
                "name": jd_name,
                "category": jd_skill.get("category", ""),
                "in_resume": True,
                "in_jd": True,
                "match_type": "exact",
                "normalized_from": None,
            })
        elif jd_lower in normalized_variants:
            matched.append({
                "name": jd_name,
                "category": jd_skill.get("category", ""),
                "in_resume": True,
                "in_jd": True,
                "match_type": "exact",
                "normalized_from": normalized_variants[jd_lower],
            })
        else:
            partial_found = False
            for r_lower, r_skill in resume_lower.items():
                r_name = r_skill.get("name", "")
                if (jd_lower in r_lower or r_lower in jd_lower) and len(jd_lower) >= 3 and len(r_lower) >= 3:
                    partial.append({
                        "name": jd_name,
                        "category": jd_skill.get("category", ""),
                        "in_resume": True,
                        "in_jd": True,
                        "match_type": "partial",
                        "normalized_from": r_name,
                    })
                    partial_found = True
                    break

            if not partial_found:
                missing.append({
                    "name": jd_name,
                    "category": jd_skill.get("category", ""),
                    "in_resume": False,
                    "in_jd": True,
                    "match_type": "missing",
                    "normalized_from": None,
                })

    return matched, missing, partial


def _compute_skill_relevance(
    matched: List[Dict[str, Any]],
    missing: List[Dict[str, Any]],
    partial: List[Dict[str, Any]],
    resume_skills: List[Dict[str, Any]],
    jd_skills: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute skill relevance metrics by category."""
    total_jd = len(jd_skills)
    total_resume = len(resume_skills)
    matched_count = len(matched)
    missing_count = len(missing)

    match_pct = round((matched_count / total_jd) * 100, 1) if total_jd > 0 else 0.0

    by_category: Dict[str, Dict[str, int]] = {}
    for item in matched:
        cat = item.get("category", "uncategorized")
        if cat not in by_category:
            by_category[cat] = {"matched": 0, "total": 0}
        by_category[cat]["matched"] = by_category[cat].get("matched", 0) + 1

    for item in jd_skills:
        cat = item.get("category", "uncategorized")
        if cat not in by_category:
            by_category[cat] = {"matched": 0, "total": 0}
        by_category[cat]["total"] = by_category[cat].get("total", 0) + 1

    return {
        "matched_count": matched_count,
        "missing_count": missing_count,
        "total_jd_skills": total_jd,
        "total_resume_skills": total_resume,
        "match_percentage": match_pct,
        "by_category": by_category,
    }


def _compute_keyword_match(
    resume_keywords: List[str],
    jd_keywords: List[str],
) -> Dict[str, Any]:
    """Compute keyword match metrics."""
    resume_set = set(resume_keywords)
    jd_set = set(jd_keywords)

    matched = sorted(resume_set & jd_set)
    missing = sorted(jd_set - resume_set)
    total = len(jd_set)
    match_count = len(matched)
    match_pct = round((match_count / total) * 100, 1) if total > 0 else 0.0

    return {
        "matched_keywords": matched,
        "missing_keywords": missing,
        "jd_keywords": sorted(jd_set),
        "resume_keywords": sorted(resume_set),
        "match_count": match_count,
        "total_count": total,
        "match_percentage": match_pct,
    }


def _compute_overall_score(
    skill_match_pct: float,
    keyword_match_pct: float,
    has_experience: bool,
    has_jd_skills: bool,
    has_jd_keywords: bool,
) -> int:
    """Compute weighted overall match score.

    Returns 0 when JD has no extractable skills or keywords to match against.
    """
    if not has_jd_skills and not has_jd_keywords:
        return 0
    if not has_experience:
        return int(round(skill_match_pct * 0.6 + keyword_match_pct * 0.4))
    return int(round(skill_match_pct * 0.5 + keyword_match_pct * 0.3 + 20 * 0.2))


def compute_jd_match(
    resume: Dict[str, Any],
    jd_text: str,
) -> Dict[str, Any]:
    """Compute deterministic resume-to-JD match.

    Args:
        resume: Structured resume data (camelCase or snake_case)
        jd_text: Job description text

    Returns:
        Dictionary with match results
    """
    normalized = _normalize_resume_for_matching(resume)

    jd_skills = _extract_skills_from_jd(jd_text)
    jd_keywords = _extract_keywords(jd_text)

    resume_skills = _get_resume_skills(normalized)

    resume_text_parts = []
    for exp in normalized.get("experience") or []:
        if isinstance(exp, dict):
            desc = exp.get("description") or ""
            if isinstance(desc, str):
                resume_text_parts.append(desc)
    summary = normalized.get("summary") or ""
    if isinstance(summary, str):
        resume_text_parts.append(summary)
    for proj in normalized.get("projects") or []:
        if isinstance(proj, dict):
            desc = proj.get("description") or ""
            if isinstance(desc, str):
                resume_text_parts.append(desc)
    resume_text = " ".join(resume_text_parts)
    resume_keywords = _extract_keywords(resume_text)

    matched_skills, missing_skills, partial_matches = _match_skills(resume_skills, jd_skills)

    skill_relevance = _compute_skill_relevance(
        matched_skills, missing_skills, partial_matches,
        resume_skills, jd_skills,
    )

    keyword_match = _compute_keyword_match(resume_keywords, jd_keywords)

    jd_years = _extract_jd_year_requirement(jd_text)
    resume_years, domains = _calculate_experience_years(normalized)

    has_experience = len(normalized.get("experience") or []) > 0
    has_jd_skills = len(jd_skills) > 0
    has_jd_keywords = len(jd_keywords) > 0

    overall_score = _compute_overall_score(
        skill_relevance["match_percentage"],
        keyword_match["match_percentage"],
        has_experience,
        has_jd_skills,
        has_jd_keywords,
    )

    experience_relevance = {
        "score": min(100, resume_years * 20) if jd_years > 0 else 50,
        "relevant_years_demanded": jd_years if jd_years > 0 else None,
        "relevant_years_supplied": resume_years,
        "matched_domains": list(domains)[:10],
        "assessment": "",
    }

    if jd_years > 0 and resume_years >= jd_years:
        experience_relevance["assessment"] = (
            f"Resume meets the {jd_years}-year experience requirement "
            f"({resume_years} years)."
        )
        experience_relevance["score"] = min(100, int((resume_years / jd_years) * 100))
    elif jd_years > 0:
        experience_relevance["assessment"] = (
            f"Resume has {resume_years} years, below the {jd_years}-year "
            f"requirement."
        )
        experience_relevance["score"] = max(0, min(100, int((resume_years / jd_years) * 100)))
    else:
        experience_relevance["assessment"] = (
            f"Resume has {resume_years} years of experience."
        )

    recommendations = []
    if keyword_match["match_percentage"] < 50:
        recommendations.append(
            "Incorporate more job-specific keywords from the description "
            "into your resume."
        )
    if skill_relevance["match_percentage"] < 50:
        recommendations.append(
            "Add missing technical skills that the job description emphasizes."
        )
    if missing_skills and len(missing_skills) <= 5:
        names = [s["name"] for s in missing_skills]
        recommendations.append(
            f"Consider adding these missing skills: {', '.join(names)}."
        )
    if jd_years > 0 and resume_years < jd_years:
        recommendations.append(
            f"Highlight relevant experience to bridge the {jd_years}-year "
            f"experience gap."
        )
    if not recommendations:
        recommendations.append("Your resume aligns well with this job description.")

    return {
        "overall_match_score": overall_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "partial_matches": partial_matches,
        "keyword_matches": keyword_match,
        "keyword_gaps": keyword_match["missing_keywords"],
        "experience_relevance": experience_relevance,
        "skill_relevance": skill_relevance,
        "recommendations": recommendations,
        "deterministic": {
            "overall_score": overall_score,
            "skill_match": skill_relevance,
            "keyword_match": keyword_match,
            "experience_relevance": experience_relevance,
        },
    }
