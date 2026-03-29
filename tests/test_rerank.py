"""Tests for re-ranking (FlashRank wrapper)."""

from __future__ import annotations

import pytest
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from pinrag.rag.rerank import is_rerank_available, wrap_retriever_with_rerank


def test_is_rerank_available_without_flashrank_dep() -> None:
    """When flashrank dep is missing, is_rerank_available returns (False, message)."""
    available, err = is_rerank_available()
    if available:
        pytest.skip("flashrank installed; missing-dependency path unavailable")
    assert err is not None
    assert "flashrank" in err or "not installed" in err


def test_is_rerank_available_with_flashrank_installed() -> None:
    """When flashrank is installed, returns (True, None)."""
    available, err = is_rerank_available()
    if not available:
        pytest.skip(err or "flashrank unavailable")
    assert available is True
    assert err is None


def test_wrap_retriever_with_rerank_returns_retriever() -> None:
    """wrap_retriever_with_rerank returns a retriever (requires flashrank)."""
    class FakeRetriever(BaseRetriever):
        def _get_relevant_documents(
            self,
            query: str,
            *,
            run_manager: CallbackManagerForRetrieverRun | None = None,
        ) -> list[Document]:
            return [
                Document(page_content="doc1", metadata={"page": 1}),
                Document(page_content="doc2", metadata={"page": 2}),
            ]

    available, err = is_rerank_available()
    if not available:
        pytest.skip(err or "rerank dependencies unavailable")

    wrapped = wrap_retriever_with_rerank(FakeRetriever(), top_n=2)
    assert wrapped is not None
    # Invoking would run FlashRank scoring; we just verify the wrapper was created
