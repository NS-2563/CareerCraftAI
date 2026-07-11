"""Prompts for summary generation and improvement."""
from typing import Dict, Any

from app.utils.prompt_builder import build_prompt, format_resume_section


def generate_summary_prompt(personal: Dict[str, Any]) -> str:
    """Generate a prompt for creating a professional summary.

    Args:
        personal: Dictionary containing personal information

    Returns:
        Formatted prompt string
    """
    parts = []

    # Basic info
    if personal.get("first_name") or personal.get("last_name"):
        name = f"{personal.get('first_name', '')} {personal.get('last_name', '')}".strip()
        parts.append(f"Name: {name}")

    if personal.get("email"):
        parts.append(f"Email: {personal.get('email')}")

    if personal.get("phone"):
        parts.append(f"Phone: {personal.get('phone')}")

    if personal.get("location"):
        parts.append(f"Location: {personal.get('location')}")

    # Experience
    if personal.get("experience"):
        parts.append("\nExperience:")
        for exp in personal.get("experience", []):
            parts.append(format_resume_section(exp))

    # Education
    if personal.get("education"):
        parts.append("\nEducation:")
        for edu in personal.get("education", []):
            parts.append(format_resume_section(edu))

    # Skills
    if personal.get("skills"):
        skills_text = ", ".join(
            s.get("name", s) if isinstance(s, dict) else s
            for s in personal.get("skills", [])
        )
        parts.append(f"\nSkills: {skills_text}")

    # Projects
    if personal.get("projects"):
        parts.append("\nProjects:")
        for proj in personal.get("projects", []):
            parts.append(format_resume_section(proj))

    context = "\n".join(parts) if parts else "No resume data provided"

    return build_prompt(
        task="Generate a professional summary for a resume.",
        context=context,
        requirements=[
            "2-4 sentences long",
            "Professional tone",
            "Highlight key skills and experience",
            "Include quantified achievements if available",
            "End with career objective or value proposition",
            "ATS-friendly (no special characters)",
        ],
        output_format="Just the summary text, no additional explanation",
    )


def improve_summary_prompt(summary: str) -> str:
    """Generate a prompt for improving an existing summary.

    Args:
        summary: The original summary text

    Returns:
        Formatted prompt string
    """
    return build_prompt(
        task="Improve the following resume summary to make it more impactful.",
        context=f"Current summary:\n{summary}",
        requirements=[
            "Use strong action verbs",
            "Include quantifiable achievements where possible",
            "Remove jargon and clichés",
            "Keep it 2-4 sentences",
            "Make it ATS-friendly",
            "Focus on unique value proposition",
        ],
        output_format="Just the improved summary text, no additional explanation",
    )