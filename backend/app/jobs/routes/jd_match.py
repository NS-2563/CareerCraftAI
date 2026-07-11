from fastapi import APIRouter

router = APIRouter()

@router.post("/match-jd")
def match_jd(data: dict):

    resume_skills = data["resume_skills"]
    jd_skills = data["jd_skills"]

    resume_lower = [s.lower() for s in resume_skills]
    jd_lower = [s.lower() for s in jd_skills]

    matched = []
    missing = []

    for skill in jd_skills:
        if skill.lower() in resume_lower:
            matched.append(skill)
        else:
            missing.append(skill)

    score = round(len(matched) / len(jd_skills) * 100, 2)

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "match_score": score
    }