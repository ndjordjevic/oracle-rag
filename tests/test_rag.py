"""Tests for the RAG chain: formatting, prompt, and full chain."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun

from pinrag.rag import RAG_PROMPT, format_docs, format_sources, run_rag
from pinrag.rag.prompts import get_rag_prompt

from pinrag.llm import get_chat_model
from pinrag.vectorstore import create_retriever


def test_format_docs_empty() -> None:
    """format_docs with no documents returns a fallback message."""
    assert "No relevant" in format_docs([])


def test_format_docs_numbered() -> None:
    """format_docs with number_chunks=True adds [N] and doc/page labels."""
    docs = [
        Document(page_content="First chunk.", metadata={"document_id": "a.pdf", "page": 1}),
        Document(page_content="Second chunk.", metadata={"document_id": "a.pdf", "page": 2}),
    ]
    out = format_docs(docs, number_chunks=True)
    assert "[1]" in out and "[2]" in out
    assert "doc: a.pdf" in out and "p. 1" in out and "p. 2" in out
    assert "First chunk." in out and "Second chunk." in out


def test_format_docs_unnumbered() -> None:
    """format_docs with number_chunks=False omits labels."""
    docs = [
        Document(page_content="Only text.", metadata={"page": 1}),
    ]
    out = format_docs(docs, number_chunks=False)
    assert "[1]" not in out
    assert "Only text." in out


def test_format_sources_empty() -> None:
    """format_sources with no docs returns empty list."""
    assert format_sources([]) == []


def test_format_sources_dedup() -> None:
    """format_sources deduplicates by (document_id, page)."""
    docs = [
        Document(page_content="x", metadata={"document_id": "f.pdf", "page": 1}),
        Document(page_content="y", metadata={"document_id": "f.pdf", "page": 1}),
        Document(page_content="z", metadata={"document_id": "f.pdf", "page": 2}),
    ]
    sources = format_sources(docs)
    assert len(sources) == 2
    assert sources[0] == {"document_id": "f.pdf", "page": 1}
    assert sources[1] == {"document_id": "f.pdf", "page": 2}


def test_rag_prompt_has_context_and_question() -> None:
    """RAG prompt template has placeholders for context and question."""
    prompt_value = RAG_PROMPT.invoke({"context": "some context", "question": "What?"})
    # PromptValue has .messages (list of (role, content) or Message-like).
    parts = []
    for m in prompt_value.messages:
        if hasattr(m, "content"):
            parts.append(str(m.content))
        elif isinstance(m, (list, tuple)) and len(m) >= 2:
            parts.append(str(m[1]))
        else:
            parts.append(str(m))
    text = " ".join(parts)
    assert "some context" in text
    assert "What?" in text


def test_concise_prompt_style_includes_concise_instruction() -> None:
    """Concise prompt mode includes concise-response guidance."""
    prompt_value = get_rag_prompt("concise").invoke(
        {"context": "ctx", "question": "q"}
    )
    text = " ".join(
        str(m.content) if hasattr(m, "content") else str(m)
        for m in prompt_value.messages
    )
    assert "Keep the response concise" in text


def test_prompt_includes_internal_reasoning_instruction() -> None:
    """Prompt includes internal step-by-step guidance (not exposed)."""
    prompt_value = get_rag_prompt("thorough").invoke(
        {"context": "ctx", "question": "q"}
    )
    text = " ".join(
        str(m.content) if hasattr(m, "content") else str(m)
        for m in prompt_value.messages
    )
    assert "Think step-by-step internally" in text


def test_rag_chain_invoke(tmp_path: Path) -> None:
    """Full RAG pipeline: index a PDF, run a query, get answer and sources."""
    from dotenv import load_dotenv
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set; skipping RAG chain test")

    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present")

    from pinrag.indexing import index_pdf
    from pinrag.embeddings import get_embedding_model

    persist_dir = tmp_path / "chroma_rag"
    index_pdf(
        sample_pdf,
        persist_directory=str(persist_dir),
        collection_name="rag_test",
        embedding=get_embedding_model(),
    )
    llm = get_chat_model()
    result = run_rag(
        "What is this document about? One short sentence.",
        llm,
        k=3,
        persist_directory=str(persist_dir),
        collection_name="rag_test",
        embedding=get_embedding_model(),
    )
    assert hasattr(result, "answer")
    assert hasattr(result, "sources")
    assert isinstance(result.answer, str)
    assert len(result.answer.strip()) > 0
    assert isinstance(result.sources, list)


def test_run_rag_with_retriever(tmp_path: Path) -> None:
    """run_rag accepts a retriever directly (uses create_retriever under the hood)."""
    from dotenv import load_dotenv
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set; skipping RAG test")

    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present")

    from pinrag.indexing import index_pdf
    from pinrag.embeddings import get_embedding_model

    persist_dir = tmp_path / "chroma_rag"
    index_pdf(
        sample_pdf,
        persist_directory=str(persist_dir),
        collection_name="rag_test",
        embedding=get_embedding_model(),
    )
    retriever = create_retriever(
        k=3,
        persist_directory=str(persist_dir),
        collection_name="rag_test",
        embedding=get_embedding_model(),
    )
    llm = get_chat_model()
    result = run_rag(
        "What is this document about? One short sentence.",
        llm,
        retriever=retriever,
    )
    assert hasattr(result, "answer")
    assert hasattr(result, "sources")
    assert isinstance(result.answer, str)
    assert len(result.answer.strip()) > 0


def test_run_rag_zero_retrieval_returns_clear_message() -> None:
    """When retrieval returns 0 docs, run_rag returns a clear message without calling LLM."""
    class EmptyRetriever(BaseRetriever):
        def _get_relevant_documents(
            self, query: str, *, run_manager: CallbackManagerForRetrieverRun | None = None
        ) -> list[Document]:
            return []

    retriever = EmptyRetriever()
    llm = get_chat_model()
    result = run_rag("any question", llm, retriever=retriever)
    assert "No relevant passages found" in result.answer
    assert result.sources == []


def test_run_rag_with_multi_query(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """run_rag with PINRAG_USE_MULTI_QUERY=true returns valid RAGResult."""
    from dotenv import load_dotenv
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("No LLM API key; skipping multi-query integration test")

    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present")

    from pinrag.indexing import index_pdf
    from pinrag.embeddings import get_embedding_model

    monkeypatch.setenv("PINRAG_USE_MULTI_QUERY", "true")
    monkeypatch.delenv("PINRAG_USE_RERANK", raising=False)

    persist_dir = tmp_path / "chroma_mq"
    index_pdf(
        sample_pdf,
        persist_directory=str(persist_dir),
        collection_name="rag_mq_test",
        embedding=get_embedding_model(),
    )
    llm = get_chat_model()
    result = run_rag(
        "What is this document about?",
        llm,
        k=3,
        persist_directory=str(persist_dir),
        collection_name="rag_mq_test",
        embedding=get_embedding_model(),
    )
    assert hasattr(result, "answer")
    assert hasattr(result, "sources")
    assert isinstance(result.answer, str)
    assert len(result.answer.strip()) > 0
    assert isinstance(result.sources, list)


def test_run_rag_use_rerank_false_uses_normal_retrieval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With use_rerank=False (or unset), run_rag uses normal retriever; no crash."""
    monkeypatch.delenv("PINRAG_USE_RERANK", raising=False)
    monkeypatch.delenv("COHERE_API_KEY", raising=False)

    class FakeRetriever(BaseRetriever):
        def _get_relevant_documents(
            self, query: str, *, run_manager: CallbackManagerForRetrieverRun | None = None
        ) -> list[Document]:
            return [
                Document(
                    page_content="Context here.",
                    metadata={"document_id": "x.pdf", "page": 1},
                )
            ]

    llm = __import__("pinrag.llm", fromlist=["get_chat_model"]).get_chat_model()
    result = run_rag(
        "test question",
        llm,
        retriever=FakeRetriever(),
        use_rerank=False,
    )
    assert result.answer
    assert len(result.sources) == 1


def test_run_rag_use_rerank_true_no_cohere_falls_back(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """With use_rerank=True but COHERE_API_KEY missing, rerank is disabled and normal retrieval is used (no crash)."""
    monkeypatch.setenv("PINRAG_USE_RERANK", "true")
    monkeypatch.delenv("COHERE_API_KEY", raising=False)

    # Use empty Chroma - we get "No relevant passages" but no crash
    llm = __import__("pinrag.llm", fromlist=["get_chat_model"]).get_chat_model()
    result = run_rag(
        "any question",
        llm,
        retriever=None,
        k=5,
        persist_directory=str(tmp_path / "chroma_empty"),
        collection_name="empty_rerank_test",
    )
    assert "No relevant passages found" in result.answer
    assert result.sources == []


def test_run_rag_use_rerank_override_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Passing use_rerank=False overrides env PINRAG_USE_RERANK=true."""
    monkeypatch.setenv("PINRAG_USE_RERANK", "true")
    monkeypatch.delenv("COHERE_API_KEY", raising=False)

    class FakeRetriever(BaseRetriever):
        def _get_relevant_documents(
            self, query: str, *, run_manager: CallbackManagerForRetrieverRun | None = None
        ) -> list[Document]:
            return [
                Document(
                    page_content="Override test.",
                    metadata={"document_id": "y.pdf", "page": 2},
                )
            ]

    llm = __import__("pinrag.llm", fromlist=["get_chat_model"]).get_chat_model()
    result = run_rag(
        "override test",
        llm,
        retriever=FakeRetriever(),
        use_rerank=False,
    )
    assert result.answer
    assert len(result.sources) == 1


def test_run_rag_llm_failure_returns_graceful_message() -> None:
    """When LLM invoke fails, run_rag returns a short error message instead of raising."""
    from unittest.mock import MagicMock

    class FakeRetriever(BaseRetriever):
        def _get_relevant_documents(
            self, query: str, *, run_manager: CallbackManagerForRetrieverRun | None = None
        ) -> list[Document]:
            return [
                Document(page_content="Some context.", metadata={"document_id": "a.pdf", "page": 1})
            ]

    llm = MagicMock()
    llm.invoke.side_effect = Exception("Rate limit exceeded")
    result = run_rag("any question", llm, retriever=FakeRetriever())
    assert "Answer generation failed" in result.answer
    assert "rate limit" in result.answer.lower()
    assert result.sources == []


def test_run_rag_multiple_pdfs_document_id_and_tag_filters(tmp_path: Path) -> None:
    """Integration: index 2 PDFs (different tags), query with document_id and tag; verify cross-document retrieval."""
    from dotenv import load_dotenv
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set; skipping multi-PDF integration test")

    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present; skipping multi-PDF integration test")

    from pinrag.indexing import index_pdf
    from pinrag.embeddings import get_embedding_model

    # Two "documents" from same content so we have distinct document_ids and tags
    doc_a = tmp_path / "doc_alpha.pdf"
    doc_b = tmp_path / "doc_beta.pdf"
    shutil.copy(sample_pdf, doc_a)
    shutil.copy(sample_pdf, doc_b)

    persist_dir = tmp_path / "chroma_multi"
    embedding = get_embedding_model()
    index_pdf(doc_a, persist_directory=str(persist_dir), collection_name="multi_test", embedding=embedding, tag="alpha")
    index_pdf(doc_b, persist_directory=str(persist_dir), collection_name="multi_test", embedding=embedding, tag="beta")

    llm = get_chat_model()

    # Query restricted to doc_alpha.pdf by document_id — all sources must be from that doc
    result_a = run_rag(
        "What is this document about? One short sentence.",
        llm,
        k=3,
        persist_directory=str(persist_dir),
        collection_name="multi_test",
        embedding=embedding,
        document_id="doc_alpha.pdf",
    )
    assert result_a.answer
    assert result_a.sources
    for s in result_a.sources:
        assert s.get("document_id") == "doc_alpha.pdf", f"Expected only doc_alpha.pdf, got {s}"

    # Query restricted to tag beta — all sources must be from doc_beta.pdf
    result_beta = run_rag(
        "Summarize in one sentence.",
        llm,
        k=3,
        persist_directory=str(persist_dir),
        collection_name="multi_test",
        embedding=embedding,
        tag="beta",
    )
    assert result_beta.answer
    assert result_beta.sources
    for s in result_beta.sources:
        assert s.get("document_id") == "doc_beta.pdf", f"Expected only doc_beta.pdf, got {s}"

    # Unfiltered query — should return answer and sources from either doc
    result_any = run_rag(
        "What is this document about?",
        llm,
        k=4,
        persist_directory=str(persist_dir),
        collection_name="multi_test",
        embedding=embedding,
    )
    assert result_any.answer
    assert result_any.sources
    doc_ids = {s.get("document_id") for s in result_any.sources}
    assert doc_ids <= {"doc_alpha.pdf", "doc_beta.pdf"}
