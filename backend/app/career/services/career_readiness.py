from typing import Dict


def calculate_career_readiness(
    ats_score: float,
    skill_match: float,
    sections_found: Dict[str, bool],
) -> dict:
    """
    Calculate an overall career readiness score.

    Components:
    - ATS Score (40%)
    - Skill Match (30%)
    - Projects (15%)
    - Certifications (15%)
    """

    ats_score = max(0, min(float(ats_score), 100))
    skill_match = max(0, min(float(skill_match), 100))

    projects_score = (
        100
        if sections_found.get("projects", False)
        else 0
    )

    certification_score = (
        100
        if sections_found.get("certifications", False)
        else 0
    )

    readiness = (
        ats_score * 0.40
        + skill_match * 0.30
        + projects_score * 0.15
        + certification_score * 0.15
    )

    readiness = round(readiness, 2)

    if readiness >= 80:
        status = "Job Ready"

    elif readiness >= 60:
        status = "Moderately Job Ready"

    else:
        status = "Needs Improvement"

    return {
        "career_readiness_score": readiness,
        "status": status,
    }