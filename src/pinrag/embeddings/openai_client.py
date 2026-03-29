"""Embedding clients for RAG (OpenAI).

Implementation lives in this module for historical import paths
(`pinrag.embeddings.openai_client`); `get_embedding_model` dispatches by
``PINRAG_EMBEDDING_PROVIDER``.
"""

from __future__ import annotations

import os

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

from pinrag.config import (
    DEFAULT_EMBEDDING_MODEL_OPENAI,
    get_embedding_model_name,
)

# For tests and backward compatibility.
DEFAULT_MODEL = DEFAULT_EMBEDDING_MODEL_OPENAI


def get_embedding_model(
    *,
    model: str | None = None,
    api_key: str | None = None,
) -> Embeddings:
    """Return an embedding model based on PINRAG_EMBEDDING_PROVIDER (openai).

    For openai, requires OPENAI_API_KEY unless ``api_key`` is passed.

    Embedding provider options:
    - openai: text-embedding-3-small, text-embedding-3-large (default: text-embedding-3-small)
    """
    model_name = model if model is not None else get_embedding_model_name()

    key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings.")
    return OpenAIEmbeddings(model=model_name, api_key=SecretStr(key))
