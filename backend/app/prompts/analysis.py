"""Prompts for resume analysis."""
from typing import Dict, Any

from app.utils.prompt_builder import build_prompt, format_resume_section


def analyze_resume_prompt(resume: Dict[str, Any]) -> str:
    """Generate a prompt for analyzing a resume.

    Args:
        resume: Complete resume data dictionary

    Returns:
        Formatted prompt string
    """
    parts = []

    # Summary
    if resume.get("summary"):
        parts.append(f"Summary: {resume.get('summary')}")

    # Personal info
    if resume.get("personal"):
        parts.append("\nPersonal Information:")
        parts.append(format_resume_section(resume.get("personal")))

    # Experience
    if resume.get("experience"):
        parts.append("\nExperience:")
        for exp in resume.get("experience", []):
            parts.append(format_resume_section(exp))

    # Education
    if resume.get("education"):
        parts.append("\nEducation:")
        for edu in resume.get("education", []):
            parts.append(format_resume_section(edu))

    # Skills
    if resume.get("skills"):
        parts.append("\nSkills:")
        for skill in resume.get("skills", []):
            parts.append(format_resume_section(skill))

    # Projects
    if resume.get("projects"):
        parts.append("\nProjects:")
        for proj in resume.get("projects", []):
            parts.append(format_resume_section(proj))

    # Certifications
    if resume.get("certifications"):
        parts.append("\nCertifications:")
        for cert in resume.get("certifications", []):
            parts.append(format_resume_section(cert))

    context = "\n".join(parts) if parts else "No resume data provided"

    return build_prompt(
        task="Analyze the following resume and provide comprehensive feedback.",
        context=context,
        requirements=[
            "Score overall resume quality (0-100)",
            "Score ATS compatibility (0-100)",
            "Identify strengths and weaknesses",
            "Suggest specific improvements",
            "Check for quantifiable achievements",
            "Verify action verb usage",
            "Check forKeywords optimization",
        ],
        output_format='Return as JSON: {"resume_score": 75, "ats_score": 80, "suggestions": [], "strengths": [], "weaknesses": []}',
    )