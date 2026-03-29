"""Shared API-key hints for `scripts/` CLIs."""

from __future__ import annotations

import os

_KEY_HINT = "Set it in your shell or add it to the MCP server `env` map in mcp.json."


def llm_keys_error_message() -> str | None:
    """Return an error message if the configured LLM provider's API key is missing."""
    from pinrag.config import get_llm_provider

    provider = get_llm_provider()
    if provider == "anthropic":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return (
                "ANTHROPIC_API_KEY is not set (PINRAG_LLM_PROVIDER=anthropic). "
                + _KEY_HINT
            )
        return None
    if provider == "openrouter":
        if not os.environ.get("OPENROUTER_API_KEY"):
            return (
                "OPENROUTER_API_KEY is not set (PINRAG_LLM_PROVIDER=openrouter). "
                + _KEY_HINT
            )
        return None
    if not os.environ.get("OPENAI_API_KEY"):
        return "OPENAI_API_KEY is not set (PINRAG_LLM_PROVIDER=openai). " + _KEY_HINT
    return None


def rag_keys_error_message() -> str | None:
    """Return an error message if the LLM API key is missing for RAG.

    Embeddings run locally (Nomic) and do not require an API key.
    """
    return llm_keys_error_message()
