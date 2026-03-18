"""Startup validation for required API keys based on configured providers."""

from __future__ import annotations

import logging
import os
import sys

from pinrag.config import get_embedding_provider, get_llm_provider

_LOG = logging.getLogger("pinrag.env_validation")

_ENV_HINT = "Set it in .env (cwd or ~/.config/pinrag/ or ~/.pinrag/) or in the environment."


def require_embedding_api_key() -> None:
    """Verify the embedding provider's API key is set. Exit with error if missing."""
    provider = get_embedding_provider()
    if provider == "openai":
        if not os.environ.get("OPENAI_API_KEY"):
            _LOG.error(
                "OPENAI_API_KEY not set. It is required when PINRAG_EMBEDDING_PROVIDER=openai. %s",
                _ENV_HINT,
            )
            sys.exit(1)
    elif provider == "cohere":
        if not os.environ.get("COHERE_API_KEY"):
            _LOG.error(
                "COHERE_API_KEY not set. It is required when PINRAG_EMBEDDING_PROVIDER=cohere. %s",
                _ENV_HINT,
            )
            sys.exit(1)


def require_llm_api_key() -> None:
    """Verify the LLM provider's API key is set. Exit with error if missing."""
    provider = get_llm_provider()
    if provider == "anthropic":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            _LOG.error(
                "ANTHROPIC_API_KEY not set. It is required when PINRAG_LLM_PROVIDER=anthropic. %s",
                _ENV_HINT,
            )
            sys.exit(1)
    elif provider == "openai":
        if not os.environ.get("OPENAI_API_KEY"):
            _LOG.error(
                "OPENAI_API_KEY not set. It is required when PINRAG_LLM_PROVIDER=openai. %s",
                _ENV_HINT,
            )
            sys.exit(1)


def require_api_keys_for_server() -> None:
    """Verify both embedding and LLM API keys are set. Exit with error if any are missing."""
    require_embedding_api_key()
    require_llm_api_key()
