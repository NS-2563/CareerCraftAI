def calculate_jd_match(
    resume_skills,
    jd_skills
):
    matched = []
    missing = []

    for skill in jd_skills:
        if skill in resume_skills:
            matched.append(skill)
        else:
            missing.append(skill)

    score = (
        len(matched) /
        len(jd_skills) * 100
        if jd_skills else 0
    )

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "match_score": round(score,2)
    }