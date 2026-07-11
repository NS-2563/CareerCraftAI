"""Prompts for skills suggestion."""
from typing import List, Optional, Dict, Any

from app.utils.prompt_builder import build_prompt


def suggest_skills_prompt(
    current_skills: List[str],
    job_title: Optional[str] = None,
    job_description: Optional[str] = None,
) -> str:
    """Generate a prompt for suggesting relevant skills.

    Args:
        current_skills: List of current skills
        job_title: Target job title
        job_description: Target job description

    Returns:
        Formatted prompt string
    """
    parts = []

    if current_skills:
        skills_str = ", ".join(current_skills)
        parts.append(f"Current skills: {skills_str}")

    if job_title:
        parts.append(f"Target job title: {job_title}")

    if job_description:
        parts.append(f"\nJob description:\n{job_description}")

    context = "\n".join(parts) if parts else "No data provided"

    return build_prompt(
        task="Suggest relevant skills to add to a resume based on target job.",
        context=context,
        requirements=[
            "Suggest both technical and soft skills",
            "Prioritize skills that are in high demand",
            "Include skills that complement current expertise",
            "Categorize by: technical, soft_skills, tools",
            "Keep list to 5-10 new skills",
        ],
        output_format='Return as JSON: {"skills": ["skill1", "skill2"], "categories": {"technical": [], "soft_skills": [], "tools": []}}',
    )