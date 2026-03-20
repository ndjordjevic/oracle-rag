"""Shared API-key hints for `scripts/` CLIs."""

from __future__ import annotations

import os

_KEY_HINT = "Set it in your shell or add it to the MCP server `env` map in mcp.json."


def llm_keys_error_message() -> str | None:
    """Return an error message if the configured LLM provider's API key is missing."""
    from pinrag.config import get_llm_provider

    if get_llm_provider() == "anthropic":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return (
                "ANTHROPIC_API_KEY is not set (PINRAG_LLM_PROVIDER=anthropic). "
                + _KEY_HINT
            )
    elif not os.environ.get("OPENAI_API_KEY"):
        return (
            "OPENAI_API_KEY is not set (PINRAG_LLM_PROVIDER=openai). " + _KEY_HINT
        )
    return None


def embedding_keys_error_message() -> str | None:
    """Return an error message if the configured embedding provider's API key is missing."""
    from pinrag.config import get_embedding_provider

    if get_embedding_provider() == "cohere":
        if not os.environ.get("COHERE_API_KEY"):
            return (
                "COHERE_API_KEY is not set (PINRAG_EMBEDDING_PROVIDER=cohere). "
                + _KEY_HINT
            )
    elif not os.environ.get("OPENAI_API_KEY"):
        return (
            "OPENAI_API_KEY is not set (PINRAG_EMBEDDING_PROVIDER=openai). " + _KEY_HINT
        )
    return None


def rag_keys_error_message() -> str | None:
    """Return an error message if embeddings or LLM keys are missing for RAG."""
    return embedding_keys_error_message() or llm_keys_error_message()
