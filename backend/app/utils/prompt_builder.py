"""Prompt builder utility for safe prompt construction."""
from typing import Any, Dict, List, Optional


def build_prompt(
    task: str,
    context: str,
    requirements: Optional[List[str]] = None,
    output_format: Optional[str] = None,
) -> str:
    """Build a structured prompt for AI models.

    Args:
        task: The main task description
        context: Background/context information
        requirements: List of requirements
        output_format: Expected output format description

    Returns:
        Formatted prompt string
    """
    sections = [
        f"Task: {task}",
        "",
        f"Context:",
        context,
    ]

    if requirements:
        sections.extend([
            "",
            "Requirements:",
        ])
        for req in requirements:
            sections.append(f"- {req}")

    if output_format:
        sections.extend([
            "",
            "Output Format:",
            output_format,
        ])

    return "\n".join(sections)


def format_resume_section(section: Any) -> str:
    """Format a resume section (experience, education, etc.) for prompts.

    Args:
        section: Dictionary or string representing a resume section

    Returns:
        Formatted string
    """
    if section is None:
        return ""
    if isinstance(section, str):
        return section
    if not isinstance(section, dict):
        return str(section)

    # Build from dict keys
    parts = []
    for key, value in section.items():
        if value is None or value == "":
            continue
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        parts.append(f"{key}: {value}")

    return " | ".join(parts)


def inject_resume_data(prompt_template: str, data: Dict[str, Any]) -> str:
    """Safely inject resume data into a prompt template.

    Args:
        prompt_template: The prompt template string
        data: Dictionary of data to inject

    Returns:
        Prompt with data injected
    """
    # Simple placeholder replacement with safety
    result = prompt_template
    for key, value in data.items():
        placeholder = f"{{{key}}}"
        if placeholder in result:
            formatted_value = format_resume_section(value)
            result = result.replace(placeholder, formatted_value)

    return result


def safe_join(items: List[str], separator: str = ", ") -> str:
    """Safely join list items into a string.

    Args:
        items: List of items to join
        separator: Separator string

    Returns:
        Joined string
    """
    if not items:
        return ""
    return separator.join(str(item) for item in items if item)