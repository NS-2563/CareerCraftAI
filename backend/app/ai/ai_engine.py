import logging
import time

from app.ai.json_parser import extract_json, JSONParseError
from app.ai.json_validator import validate_json, JSONValidationError
from app.ai.response_repair import try_repair_json
from app.providers.factory import get_provider


logger = logging.getLogger(__name__)


class AIEngineError(Exception):
    """Raised when the AI engine fails to generate valid JSON."""
    pass


def generate_json(prompt: str, schema: dict):
    """
    Generate validated JSON from Gemini.

    Pipeline

    Gemini
        ↓
    JSON Parser
        ↓
    Response Repair
        ↓
    JSON Validator
        ↓
    Retry Once
        ↓
    Fallback
    """

    retries = 2
    last_error = None

    for attempt in range(retries):

        try:

            logger.info(
                "AI Engine attempt %s/%s",
                attempt + 1,
                retries,
            )

            provider = get_provider()
            response = provider._generate_content(prompt)

            try:

                data = extract_json(response)
                logger.info("JSON parsed successfully.")

            except JSONParseError:

                logger.warning(
                    "JSON parsing failed. Attempting automatic repair."
                )

                data = try_repair_json(response)

                logger.info("JSON repaired successfully.")

            validated = validate_json(
                data=data,
                schema=schema,
            )

            logger.info("JSON validated successfully.")

            return {
                "success": True,
                "data": validated,
            }

        except (
            JSONParseError,
            JSONValidationError,
            Exception,
        ) as e:

            last_error = e

            logger.warning(
                "AI Engine attempt %s failed: %s",
                attempt + 1,
                str(e),
            )

            if attempt < retries - 1:

                delay = 2 ** attempt

                logger.info(
                    "Retrying in %s second(s)...",
                    delay,
                )

                time.sleep(delay)

    logger.exception("AI Engine failed after all retry attempts.")

    return {
        "success": False,
        "error": {
            "code": "AI_JSON_ERROR",
            "message": "Unable to generate a valid AI response.",
        },
        "details": str(last_error),
        "data": None,
    }