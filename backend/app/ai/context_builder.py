def build_context(module: str, user_data: dict) -> str:
    """
    Build a standardized context for AI modules.

    Responsibilities:
    - Format user data consistently
    - Skip None values
    - Format lists cleanly
    - Preserve multiline text
    """

    lines = [
        "You are CareerCraft AI.",
        "",
        "Application Module:",
        module,
        "",
        "User Information:",
    ]

    for key, value in user_data.items():

        if value is None:
            continue

        if isinstance(value, list):

            if not value:
                continue

            lines.append(f"{key}:")

            for item in value:
                lines.append(f"- {item}")

            continue

        value = str(value).strip()

        if not value:
            continue

        value = value.replace("\r\n", "\n")
        value = value.replace("\r", "\n")

        lines.append(f"{key}: {value}")

    lines.extend(
        [
            "",
            "General Instructions",
            "",
            "- Return accurate information.",
            "- Avoid unnecessary explanations.",
            "- Keep responses concise but complete.",
            "- Never hallucinate.",
            "- Return only the requested format.",
        ]
    )

    return "\n".join(lines)