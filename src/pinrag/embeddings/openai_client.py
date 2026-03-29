"""Embedding client for RAG (local Nomic via langchain-nomic).

Implementation lives in this module for historical import paths
(`pinrag.embeddings.openai_client`); `get_embedding_model` returns
``NomicEmbeddings`` with ``inference_mode="local"``.
"""

from __future__ import annotations

from importlib.util import find_spec

from langchain_core.embeddings import Embeddings

from pinrag.config import DEFAULT_EMBEDDING_MODEL_LOCAL, get_embedding_model_name

# For tests and backward compatibility.
DEFAULT_MODEL = DEFAULT_EMBEDDING_MODEL_LOCAL


def get_embedding_model(
    *,
    model: str | None = None,
) -> Embeddings:
    """Return local Nomic embedding model (PINRAG_EMBEDDING_MODEL or default).

    Uses ``langchain_nomic.NomicEmbeddings`` with ``inference_mode="local"``.
    No API key; the model weights download on first use (~270 MB, cached locally).
    """
    if find_spec("langchain_nomic") is None:
        raise ImportError(
            "Local embeddings require langchain-nomic. Install with: pip install pinrag"
        )
    from langchain_nomic import NomicEmbeddings

    model_name = model if model is not None else get_embedding_model_name()
    return NomicEmbeddings(model=model_name, inference_mode="local")
