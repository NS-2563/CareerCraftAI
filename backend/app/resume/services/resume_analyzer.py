def check_resume_completeness(text):

    sections = {
        "education": False,
        "skills": False,
        "projects": False,
        "experience": False,
        "certifications": False
    }

    text = text.lower()

    for section in sections:

        if section in text:
            sections[section] = True

    score = (
        sum(sections.values()) /
        len(sections)
    ) * 100

    return {
        "sections_found": sections,
        "completeness_score": score
    }