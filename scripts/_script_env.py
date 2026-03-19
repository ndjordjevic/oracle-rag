"""Shared dotenv loading and API-key checks for `scripts/` CLIs."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parent.parent


def load_project_dotenv() -> None:
    """Load ``.env`` from the repository root (parent of ``scripts/``)."""
    load_dotenv(_REPO_ROOT / ".env")


def llm_keys_error_message() -> str | None:
    """Return an error message if the configured LLM provider's API key is missing."""
    from pinrag.config import get_llm_provider

    if get_llm_provider() == "anthropic":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return (
                "ANTHROPIC_API_KEY is not set (PINRAG_LLM_PROVIDER=anthropic). "
                "Set it in .env or the environment."
            )
    elif not os.environ.get("OPENAI_API_KEY"):
        return (
            "OPENAI_API_KEY is not set (PINRAG_LLM_PROVIDER=openai). "
            "Set it in .env or the environment."
        )
    return None


def embedding_keys_error_message() -> str | None:
    """Return an error message if the configured embedding provider's API key is missing."""
    from pinrag.config import get_embedding_provider

    if get_embedding_provider() == "cohere":
        if not os.environ.get("COHERE_API_KEY"):
            return (
                "COHERE_API_KEY is not set (PINRAG_EMBEDDING_PROVIDER=cohere). "
                "Set it in .env or the environment."
            )
    elif not os.environ.get("OPENAI_API_KEY"):
        return (
            "OPENAI_API_KEY is not set (PINRAG_EMBEDDING_PROVIDER=openai). "
            "Set it in .env or the environment."
        )
    return None


def rag_keys_error_message() -> str | None:
    """Return an error message if embeddings or LLM keys are missing for RAG."""
    return embedding_keys_error_message() or llm_keys_error_message()
