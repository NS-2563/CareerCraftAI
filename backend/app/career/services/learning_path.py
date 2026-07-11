from typing import Dict, List


DEFAULT_RESOURCES = {
    "Docker": [
        "Docker Full Course",
        "Build Docker Projects",
    ],
    "AWS": [
        "AWS Cloud Practitioner",
        "AWS Hands-on Labs",
    ],
    "React": [
        "React Fundamentals",
        "Build a React Portfolio",
    ],
    "Node.js": [
        "Node.js Crash Course",
        "Build REST APIs",
    ],
    "Python": [
        "Python Programming",
        "Build Python Projects",
    ],
    "Java": [
        "Java Fundamentals",
        "Object-Oriented Programming",
    ],
    "SQL": [
        "SQL Basics",
        "Database Design Project",
    ],
}


DEFAULT_FALLBACK = [
    "Official Documentation",
    "Beginner YouTube Tutorial",
]


def generate_learning_path(
    missing_skills: List[str],
) -> List[Dict[str, List[str]]]:
    """
    Generate a deterministic learning roadmap for missing skills.
    Used as the fallback when AI generation is unavailable.
    """

    if not missing_skills:
        return []

    roadmap = []

    for skill in sorted(set(missing_skills)):

        roadmap.append(
            {
                "skill": skill,
                "resources": DEFAULT_RESOURCES.get(
                    skill,
                    DEFAULT_FALLBACK,
                ),
            }
        )

    return roadmap