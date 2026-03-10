"""Tests for re-ranking (Cohere Re-Rank wrapper)."""

from __future__ import annotations

import pytest

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun

from pinrag.rag.rerank import is_rerank_available, wrap_retriever_with_cohere_rerank


def test_is_rerank_available_no_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """When COHERE_API_KEY is not set or deps missing, is_rerank_available returns (False, message)."""
    monkeypatch.delenv("COHERE_API_KEY", raising=False)
    available, err = is_rerank_available()
    assert available is False
    assert err is not None
    # Either API key error or langchain-cohere not installed
    assert "COHERE_API_KEY" in err or "langchain" in err or "not installed" in err


def test_is_rerank_available_with_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """When COHERE_API_KEY is set and langchain_cohere is installed, returns (True, None)."""
    monkeypatch.setenv("COHERE_API_KEY", "test-key")
    available, err = is_rerank_available()
    if not available and err and "not installed" in err:
        pytest.skip("langchain-cohere not installed; cannot test API key path")
    assert available is True
    assert err is None


def test_wrap_retriever_with_cohere_rerank_returns_retriever() -> None:
    """wrap_retriever_with_cohere_rerank returns a retriever (requires langchain_cohere)."""
    class FakeRetriever(BaseRetriever):
        def _get_relevant_documents(
            self, query: str, *, run_manager: CallbackManagerForRetrieverRun | None = None
        ) -> list[Document]:
            return [
                Document(page_content="doc1", metadata={"page": 1}),
                Document(page_content="doc2", metadata={"page": 2}),
            ]

    available, err = is_rerank_available()
    if not available:
        pytest.skip(err or "rerank dependencies unavailable")

    wrapped = wrap_retriever_with_cohere_rerank(FakeRetriever(), top_n=2)
    assert wrapped is not None
    # Invoking would call Cohere API; we just verify the wrapper was created
