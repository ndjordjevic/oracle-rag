"""Re-ranking: wrap retriever with FlashRank to improve retrieval quality."""

from __future__ import annotations

import logging
from importlib.util import find_spec

from langchain_core.retrievers import BaseRetriever

logger = logging.getLogger(__name__)

FLASHRANK_INSTALL_HINT = "pip install pinrag[rerank]"


def _flashrank_dependencies_available() -> tuple[bool, str | None]:
    """Check optional deps needed for FlashRank reranking."""
    if find_spec("flashrank") is None:
        return False, f"flashrank is not installed ({FLASHRANK_INSTALL_HINT})"
    if find_spec("langchain_classic.retrievers.contextual_compression") is None:
        return False, "langchain-classic contextual compression module is unavailable"
    return True, None


def wrap_retriever_with_rerank(
    base_retriever: BaseRetriever,
    top_n: int = 5,
) -> BaseRetriever:
    """Wrap a base retriever with FlashRank via ContextualCompressionRetriever.

    Requires flashrank (pip install pinrag[rerank]).

    Args:
        base_retriever: Retriever that fetches more chunks (e.g. k=10).
        top_n: Number of chunks to return after reranking (default: 5).

    Returns:
        ContextualCompressionRetriever wrapping base_retriever with FlashrankRerank.

    """
    available, err = _flashrank_dependencies_available()
    if not available:
        raise ImportError(f"Re-ranking requires optional dependencies: {err}")

    from langchain_classic.retrievers.contextual_compression import (
        ContextualCompressionRetriever,
    )
    from langchain_community.document_compressors import FlashrankRerank

    compressor = FlashrankRerank(top_n=top_n)
    return ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever,
    )


def is_rerank_available() -> tuple[bool, str | None]:
    """Check if FlashRank rerank can be used (package installed).

    Returns:
        (available, error_message). If available is True, error_message is None.

    """
    available, err = _flashrank_dependencies_available()
    if not available:
        return False, err

    return True, None
