"""Tests for evaluation target wiring."""

from __future__ import annotations

from langchain_core.documents import Document

import pinrag.evaluation.target as target_module
from pinrag.rag import RAGResult


def test_target_uses_documents_from_run_rag(monkeypatch) -> None:
    """pinrag_target passes retriever=None so run_rag builds retriever (and applies rerank).

    It must use the documents returned by run_rag.
    """
    expected_docs = [
        Document(page_content="ctx", metadata={"document_id": "a.pdf", "page": 1})
    ]

    monkeypatch.setattr(target_module, "get_chat_model", lambda: object())
    monkeypatch.setattr(
        target_module,
        "run_rag",
        lambda query, llm, retriever=None, **kwargs: RAGResult(
            answer=f"answer: {query}",
            sources=[{"document_id": "a.pdf", "page": 1}],
            documents=expected_docs,
        ),
    )

    out = target_module.pinrag_target({"question": "Q?"})
    assert out["answer"] == "answer: Q?"
    assert out["sources"] == [{"document_id": "a.pdf", "page": 1}]
    assert out["documents"] == expected_docs
