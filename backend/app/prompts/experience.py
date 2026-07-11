"""Prompts for experience improvement."""
from typing import Optional

from app.utils.prompt_builder import build_prompt


def improve_experience_prompt(
    description: str, position: Optional[str] = None, company: Optional[str] = None
) -> str:
    """Generate a prompt for improving experience description.

    Args:
        description: The original experience description
        position: Job position title
        company: Company name

    Returns:
        Formatted prompt string
    """
    context_parts = []
    if position:
        context_parts.append(f"Position: {position}")
    if company:
        context_parts.append(f"Company: {company}")
    context_parts.append(f"Description: {description}")

    context = "\n".join(context_parts)

    return build_prompt(
        task="Improve the following work experience description for a resume.",
        context=context,
        requirements=[
            "Use strong action verbs (led, developed, implemented, achieved)",
            "Include quantifiable metrics and results",
            "Highlight leadership and impact",
            "Show progression and growth",
            "Keep each bullet point specific and measurable",
            "Remove fluff and generic statements",
            "Use present tense for current role, past tense for past roles",
        ],
        output_format="Just the improved description, one or two sentences per bullet point",
    )