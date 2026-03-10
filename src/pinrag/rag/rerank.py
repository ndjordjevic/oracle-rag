"""Re-ranking: wrap retriever with Cohere Re-Rank to improve retrieval quality."""

from __future__ import annotations

import logging
import os
from importlib.util import find_spec
from typing import Optional

from langchain_core.retrievers import BaseRetriever

logger = logging.getLogger(__name__)

DEFAULT_RERANK_MODEL = "rerank-english-v3.0"
COHERE_INSTALL_HINT = "pip install pinrag[cohere]"


def _cohere_dependencies_available() -> tuple[bool, Optional[str]]:
    """Check optional deps needed for Cohere reranking."""
    if find_spec("langchain_cohere") is None:
        return False, f"langchain-cohere is not installed ({COHERE_INSTALL_HINT})"
    if find_spec("langchain_classic.retrievers.contextual_compression") is None:
        return False, "langchain-classic contextual compression module is unavailable"
    return True, None


def wrap_retriever_with_cohere_rerank(
    base_retriever: BaseRetriever,
    top_n: int = 5,
    model: str = DEFAULT_RERANK_MODEL,
) -> BaseRetriever:
    """Wrap a base retriever with Cohere Re-Rank via ContextualCompressionRetriever.

    Requires langchain-cohere (pip install pinrag[cohere]) and COHERE_API_KEY.

    Args:
        base_retriever: Retriever that fetches more chunks (e.g. k=10).
        top_n: Number of chunks to return after reranking (default: 5).
        model: Cohere rerank model (default: rerank-english-v3.0).

    Returns:
        ContextualCompressionRetriever wrapping base_retriever with CohereRerank.
    """
    available, err = _cohere_dependencies_available()
    if not available:
        raise ImportError(f"Re-ranking requires optional dependencies: {err}")

    from langchain_classic.retrievers.contextual_compression import (
        ContextualCompressionRetriever,
    )
    from langchain_cohere import CohereRerank

    compressor = CohereRerank(model=model, top_n=top_n)
    return ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever,
    )


def is_rerank_available() -> tuple[bool, Optional[str]]:
    """Check if Cohere rerank can be used (package installed and API key set).

    Returns:
        (available, error_message). If available is True, error_message is None.
    """
    available, err = _cohere_dependencies_available()
    if not available:
        return False, err

    if not os.environ.get("COHERE_API_KEY"):
        return False, "COHERE_API_KEY is not set"

    return True, None
