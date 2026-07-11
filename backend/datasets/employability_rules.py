def calculate_employability(
    ats_score,
    skills_count,
    completeness_score
):

    score = (
        ats_score * 0.4 +
        skills_count * 3 +
        completeness_score * 0.3
    )

    return round(min(score,100),2)