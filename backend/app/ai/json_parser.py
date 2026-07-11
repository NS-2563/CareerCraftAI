import json
import logging
import re


logger = logging.getLogger(__name__)


class JSONParseError(Exception):
    """Raised when a valid JSON object cannot be extracted."""
    pass


def extract_json(text: str):
    """
    Extract JSON from an LLM response.

    Handles:
    - Markdown code fences
    - Leading/trailing text
    - JSON objects ({})
    - JSON arrays ([])
    """

    if not isinstance(text, str):
        raise JSONParseError("AI response must be a string.")

    text = text.strip()

    if not text:
        raise JSONParseError("Empty AI response.")

    # Remove markdown code fences
    text = re.sub(r"^```[a-zA-Z0-9]*\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # Try direct parsing
    try:
        return json.loads(text)

    except json.JSONDecodeError:
        logger.debug("Direct JSON parsing failed. Attempting extraction.")

    # Find first JSON object or array
    object_start = text.find("{")
    array_start = text.find("[")

    starts = [i for i in (object_start, array_start) if i != -1]

    if not starts:
        raise JSONParseError("No JSON object or array found.")

    start = min(starts)

    if start == object_start:
        end = text.rfind("}")
    else:
        end = text.rfind("]")

    if end == -1 or end <= start:
        raise JSONParseError("Incomplete JSON detected.")

    candidate = text[start:end + 1]

    try:
        return json.loads(candidate)

    except json.JSONDecodeError as e:
        logger.debug("Extracted JSON parsing failed: %s", str(e))
        raise JSONParseError(str(e))