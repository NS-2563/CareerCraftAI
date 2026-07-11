from typing import Dict

from datasets.employability_rules import calculate_employability


def predict_employability(
    ats_score: float,
    skills_count: int,
    completeness_score: float,
) -> Dict[str, object]:
    """
    Predict employability using the deterministic scoring engine.
    """

    ats_score = max(0, min(float(ats_score), 100))
    skills_count = max(0, int(skills_count))
    completeness_score = max(0, min(float(completeness_score), 100))

    score = calculate_employability(
        ats_score=ats_score,
        skills_count=skills_count,
        completeness_score=completeness_score,
    )

    score = round(max(0, min(score, 100)), 2)

    if score >= 80:
        status = "Highly Employable"

    elif score >= 60:
        status = "Moderately Employable"

    else:
        status = "Needs Improvement"

    return {
        "score": score,
        "status": status,
    }