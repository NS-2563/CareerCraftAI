from typing import Dict, List


def generate_suggestions(
    missing_skills: List[str],
    sections_found: Dict[str, bool],
) -> List[str]:
    """
    Generate deterministic resume improvement suggestions.

    Used as the fallback when AI-generated suggestions
    are unavailable.
    """

    suggestions = []

    # Missing skills
    for skill in sorted(set(missing_skills)):
        suggestions.append(
            f"Learn and include {skill} in your resume."
        )

    # Resume sections
    section_messages = {
        "projects": "Add at least two academic or personal projects.",
        "certifications": "Include relevant certifications to strengthen your profile.",
        "skills": "Create a dedicated Skills section.",
        "experience": "Add internships, freelance work, or personal experience if available.",
        "summary": "Write a concise professional summary.",
    }

    for section, message in section_messages.items():

        if not sections_found.get(section, False):
            suggestions.append(message)

    return suggestions