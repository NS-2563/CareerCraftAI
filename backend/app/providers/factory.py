"""Provider factory for AI services."""
import logging
from typing import Optional

from app.core.config import settings
from app.providers.base import AIProvider

logger = logging.getLogger(__name__)

# Singleton provider instance
_provider: Optional[AIProvider] = None


def get_provider() -> AIProvider:
    """Get the active AI provider.

    Returns:
        The configured AI provider instance

    Raises:
        ValueError: If the provider configuration is invalid
    """
    global _provider

    if _provider is not None:
        return _provider

    provider_name = settings.AI_PROVIDER.lower()

    if provider_name == "gemini":
        from app.providers.gemini import GeminiProvider

        try:
            _provider = GeminiProvider()
            logger.info("Initialized Gemini provider")
            return _provider
        except ValueError as e:
            logger.error(f"Failed to initialize Gemini provider: {e}")
            raise
    else:
        raise ValueError(f"Unsupported AI provider: {provider_name}")


def reset_provider():
    """Reset the provider instance (useful for testing)."""
    global _provider
    _provider = None