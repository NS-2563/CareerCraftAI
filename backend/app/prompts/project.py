"""Prompts for project improvement."""
from typing import Optional

from app.utils.prompt_builder import build_prompt


def improve_project_prompt(description: str, name: Optional[str] = None) -> str:
    """Generate a prompt for improving project description.

    Args:
        description: The original project description
        name: Project name

    Returns:
        Formatted prompt string
    """
    context = f"Project: {name}\nDescription: {description}" if name else f"Description: {description}"

    return build_prompt(
        task="Improve the following project description for a resume.",
        context=context,
        requirements=[
            "Highlight technical complexity and skills used",
            "Show measurable outcomes and impact",
            "Mention team collaboration if applicable",
            "Include tools and technologies",
            "Show problem-solving abilities",
            "Keep it concise but impactful",
            "Use action verbs",
        ],
        output_format="Just the improved description, 1-2 sentences",
    )