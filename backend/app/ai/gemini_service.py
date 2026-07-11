import json
import logging
import os
import time

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GeminiServiceError(Exception):
    """Raised when Gemini cannot generate a response."""
    pass


API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise GeminiServiceError("GEMINI_API_KEY is not configured.")

genai.configure(api_key=API_KEY)

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

model = genai.GenerativeModel(MODEL_NAME)


def ask_gemini(
    prompt: str,
    expect_json: bool = False,
    retries: int = 2,
    retry_delay: int = 2,
):
    """
    Generate content from Gemini.

    Responsibilities:
    - Send prompt to Gemini
    - Retry transient failures
    - Return raw text or parsed JSON
    - Raise GeminiServiceError on failure
    """

    last_error = None

    for attempt in range(retries + 1):

        try:

            logger.info(
                "Gemini request (attempt %s/%s)",
                attempt + 1,
                retries + 1,
            )

            response = model.generate_content(prompt)

            if not response:
                raise GeminiServiceError("Empty response from Gemini.")

            if not getattr(response, "text", None):
                raise GeminiServiceError("Gemini returned no text.")

            text = response.text.strip()

            if not expect_json:
                return text

            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()

            elif text.startswith("```"):
                text = text.replace("```", "").strip()

            return json.loads(text)

        except Exception as e:

            last_error = e

            logger.warning(
                "Gemini request failed (attempt %s/%s): %s",
                attempt + 1,
                retries + 1,
                str(e),
            )

            if attempt < retries:
                time.sleep(retry_delay)

    logger.exception("Gemini request failed after all retries.")

    raise GeminiServiceError(str(last_error))