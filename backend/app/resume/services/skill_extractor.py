def extract_skills(text):

    with open("datasets/skills.txt", "r") as f:
        skills_db = [skill.strip() for skill in f.readlines()]

    found_skills = []

    text_lower = text.lower()

    for skill in skills_db:
        if skill.lower() in text_lower:
            found_skills.append(skill)

    return found_skills