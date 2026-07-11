import json
import logging
import re

from app.ai.json_parser import JSONParseError

logger = logging.getLogger(__name__)


def repair_json(text: str) -> str:
    """
    Perform safe, deterministic JSON repairs.

    This function never invents content.
    It only fixes formatting issues commonly produced by LLMs.
    """

    if not text:
        return ""

    text = text.strip()

    # Remove markdown fences
    text = re.sub(r"^```[a-zA-Z0-9]*\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # Remove UTF-8 BOM
    text = text.replace("\ufeff", "")

    # Remove trailing commas
    text = re.sub(r",(\s*[}\]])", r"\1", text)

    return text.strip()


def _looks_truncated(text: str) -> bool:
    """
    Detect obviously incomplete JSON.
    """

    return (
        text.count("{") != text.count("}")
        or text.count("[") != text.count("]")
    )


def try_repair_json(text: str):
    """
    Repair and parse JSON.

    Raises:
        JSONParseError
    """

    repaired = repair_json(text)

    if _looks_truncated(repaired):
        logger.debug("Detected truncated JSON.")
        raise JSONParseError("Incomplete JSON response.")

    try:
        return json.loads(repaired)

    except json.JSONDecodeError as e:
        logger.debug("JSON repair failed: %s", str(e))
        raise JSONParseError(str(e))