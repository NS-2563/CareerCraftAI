import json

def analyze_skill_gap(user_skills, role):

    with open("datasets/roles.json", "r") as f:
        roles = json.load(f)

    required_skills = roles.get(role, [])

    matched = []
    missing = []

    for skill in required_skills:
        if skill in user_skills:
            matched.append(skill)
        else:
            missing.append(skill)

    match_percentage = (
        len(matched) / len(required_skills) * 100
        if required_skills else 0
    )

    return {
        "role": role,
        "matched_skills": matched,
        "missing_skills": missing,
        "match_percentage": round(match_percentage, 2)
    }