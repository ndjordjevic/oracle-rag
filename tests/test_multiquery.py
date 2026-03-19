"""Tests for multi-query retrieval."""

from __future__ import annotations

import os

import pytest
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from pinrag.rag.multiquery import _get_multiquery_prompt, wrap_retriever_with_multiquery


def test_get_multiquery_prompt_has_question_variable() -> None:
    """_get_multiquery_prompt returns a prompt with question input variable."""
    prompt = _get_multiquery_prompt(4)
    assert prompt.input_variables == ["question"]
    assert "question" in prompt.template


def test_wrap_retriever_with_multiquery_returns_retriever() -> None:
    """wrap_retriever_with_multiquery returns a retriever that produces docs."""

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

    from dotenv import load_dotenv

    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("No LLM API key; skipping multi-query test")

    from pinrag.llm import get_chat_model

    base = FakeRetriever()
    llm = get_chat_model()
    wrapped = wrap_retriever_with_multiquery(
        base, llm, num_queries=2, include_original=True
    )
    assert wrapped is not None

    docs = wrapped.invoke("What is DMA?")
    assert isinstance(docs, list)
    assert len(docs) >= 1
    assert all(isinstance(d, Document) for d in docs)
