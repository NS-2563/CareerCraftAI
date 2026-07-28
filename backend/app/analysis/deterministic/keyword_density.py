"""Keyword density and coverage analysis — foundation.

Deterministic keyword analysis that can be extended in later phases
with target-role keywords and JD-based matching.

Phase 3B: Resume-only analysis.
Phases 3D/3G: Add role-specific and JD-specific keywords.
"""
import re
from typing import Any, Dict, List, Set


_COMMON_TECH_KEYWORDS = {
    "python", "java", "javascript", "typescript", "react", "angular", "vue",
    "node.js", "nodejs", "django", "flask", "fastapi", "spring", "express",
    "sql", "mysql", "postgresql", "mongodb", "redis", "graphql",
    "docker", "kubernetes", "aws", "azure", "gcp", "terraform",
    "git", "github", "gitlab", "ci/cd", "jenkins",
    "rest", "api", "microservices", "oauth", "jwt",
    "html", "css", "sass", "tailwind", "bootstrap",
    "agile", "scrum", "jira", "confluence",
    "machine learning", "deep learning", "ai", "nlp",
    "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn",
}


def extract_text_from_resume(resume: Dict[str, Any]) -> str:
    parts = []

    summary = resume.get("summary") or ""
    if isinstance(summary, str) and summary.strip():
        parts.append(summary)

    experience = resume.get("experience") or []
    if isinstance(experience, list):
        for entry in experience:
            if not isinstance(entry, dict):
                continue
            for field in ("description", "position", "company"):
                val = entry.get(field) or ""
                if isinstance(val, str) and val.strip():
                    parts.append(val)

    education = resume.get("education") or []
    if isinstance(education, list):
        for entry in education:
            if not isinstance(entry, dict):
                continue
            for field in ("degree", "institution", "field_of_study", "description"):
                val = entry.get(field) or ""
                if isinstance(val, str) and val.strip():
                    parts.append(val)

    projects = resume.get("projects") or []
    if isinstance(projects, list):
        for entry in projects:
            if not isinstance(entry, dict):
                continue
            for field in ("description", "name"):
                val = entry.get(field) or ""
                if isinstance(val, str) and val.strip():
                    parts.append(val)

    skills = resume.get("skills") or []
    if isinstance(skills, list):
        for entry in skills:
            if isinstance(entry, dict):
                name = entry.get("name") or ""
                if isinstance(name, str) and name.strip():
                    parts.append(name)
            elif isinstance(entry, str) and entry.strip():
                parts.append(entry)

    certifications = resume.get("certifications") or []
    if isinstance(certifications, list):
        for entry in certifications:
            if isinstance(entry, dict):
                for field in ("name", "issuer"):
                    val = entry.get(field) or ""
                    if isinstance(val, str) and val.strip():
                        parts.append(val)

    return " ".join(parts)


def find_keywords(text: str, keywords: Set[str]) -> Dict[str, bool]:
    text_lower = text.lower()
    result = {}
    for kw in keywords:
        result[kw] = kw in text_lower
    return result


def analyze_keyword_density(resume: Dict[str, Any], keywords: Set[str] = None) -> Dict[str, Any]:
    if keywords is None:
        keywords = _COMMON_TECH_KEYWORDS

    text = extract_text_from_resume(resume)

    if not text.strip():
        return {
            "total_words": 0,
            "keywords_found": {},
            "keyword_count": 0,
            "keyword_density": 0.0,
            "matched_keywords": [],
            "missing_common_keywords": list(keywords),
        }

    text_lower = text.lower()
    words = text_lower.split()
    total_words = len(words)

    keyword_presence = find_keywords(text, keywords)
    matched = [kw for kw, present in keyword_presence.items() if present]
    missing = [kw for kw, present in keyword_presence.items() if not present]

    keyword_count = len(matched)
    return {
        "total_words": total_words,
        "keywords_found": keyword_presence,
        "keyword_count": keyword_count,
        "keyword_density": round((keyword_count / len(keywords)) * 100, 2) if keywords else 0.0,
        "matched_keywords": matched,
        "missing_common_keywords": missing,
    }
