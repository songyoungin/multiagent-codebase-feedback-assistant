"""Langfuse-based prompt management with caching."""

import time

from langfuse import Langfuse

from common.logger import get_logger
from common.settings import settings

logger = get_logger(__name__)


class PromptManager:
    """Langfuse-based prompt manager with caching support."""

    def __init__(self) -> None:
        """Initialize Langfuse client."""
        self._client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        self._cache: dict[str, tuple[str, float]] = {}
        logger.info("PromptManager initialized with Langfuse")

    def get_prompt(self, name: str, version: int | None = None) -> str:
        """Load prompt from Langfuse with caching.

        Args:
            name: Prompt name (e.g., 'project_scanner')
            version: Prompt version (None for latest version)

        Returns:
            Prompt string

        Raises:
            Exception: When prompt cannot be loaded from Langfuse
        """
        cache_key = f"{name}:{version}" if version else name
        current_time = time.time()

        # Check cache
        if cache_key in self._cache:
            cached_prompt, cached_time = self._cache[cache_key]
            if current_time - cached_time < settings.langfuse_cache_ttl:
                logger.debug(f"Returning cached prompt for '{cache_key}'")
                return cached_prompt
            logger.debug(f"Cache expired for '{cache_key}', fetching from Langfuse")

        # Load prompt from Langfuse
        try:
            logger.info(f"Fetching prompt '{name}' (version: {version or 'latest'}) from Langfuse")
            prompt_object = self._client.get_prompt(name=name, version=version)
            prompt_content = prompt_object.prompt

            # Save to cache
            self._cache[cache_key] = (prompt_content, current_time)
            logger.info(f"Successfully loaded and cached prompt '{cache_key}'")

            return prompt_content

        except Exception as e:
            logger.error(f"Failed to fetch prompt '{name}' from Langfuse: {e}")
            raise RuntimeError(
                f"Failed to load prompt '{name}' from Langfuse. "
                f"Ensure the prompt exists in Langfuse and credentials are correct."
            ) from e

    def clear_cache(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        logger.info("Prompt cache cleared")


# Global singleton instance
prompt_manager = PromptManager()
