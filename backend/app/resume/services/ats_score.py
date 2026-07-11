def calculate_ats_score(skill_match, completeness_score):

    ats_score = (
        skill_match * 0.7 +
        completeness_score * 0.3
    )

    return round(ats_score, 2)