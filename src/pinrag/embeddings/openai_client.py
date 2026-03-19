"""Embedding client for RAG. Supports OpenAI and Cohere via config."""

from __future__ import annotations

import os

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from pinrag.config import (
    DEFAULT_EMBEDDING_MODEL_OPENAI,
    get_embedding_model_name,
    get_embedding_provider,
)

# For tests and backward compatibility.
DEFAULT_MODEL = DEFAULT_EMBEDDING_MODEL_OPENAI


def get_openai_embedding_model(
    *,
    model: str | None = None,
    api_key: str | None = None,
) -> OpenAIEmbeddings:
    """Return an OpenAI embedding model client.

    Loads .env so OPENAI_API_KEY can be set there. If api_key is passed, it
    overrides the environment variable.

    Args:
        model: OpenAI embedding model name; if None, uses config.
        api_key: Optional API key; otherwise uses OPENAI_API_KEY from env.

    Returns:
        LangChain OpenAIEmbeddings instance.

    """
    key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings.")
    model_name = model if model is not None else get_embedding_model_name()
    return OpenAIEmbeddings(model=model_name, api_key=key)


def get_embedding_model(
    *,
    model: str | None = None,
    api_key: str | None = None,
) -> Embeddings:
    """Return an embedding model based on PINRAG_EMBEDDING_PROVIDER (openai | cohere).

    For cohere, requires COHERE_API_KEY and langchain-cohere.
    For openai, requires OPENAI_API_KEY (default).

    Embedding provider options:
    - openai: text-embedding-3-small, text-embedding-3-large (default: text-embedding-3-small)
    - cohere: embed-english-v3.0, embed-english-light-v3.0, embed-multilingual-v3.0
    """
    provider = get_embedding_provider()
    model_name = model if model is not None else get_embedding_model_name()

    if provider == "cohere":
        try:
            from langchain_cohere import CohereEmbeddings
        except ImportError as e:
            raise ImportError(
                "PINRAG_EMBEDDING_PROVIDER=cohere requires langchain-cohere. "
                "Install with: pip install langchain-cohere"
            ) from e
        key = api_key if api_key is not None else os.environ.get("COHERE_API_KEY")
        if not key:
            raise ValueError("COHERE_API_KEY is required for Cohere embeddings.")
        return CohereEmbeddings(model=model_name, cohere_api_key=key)

    return get_openai_embedding_model(model=model_name, api_key=api_key)
