"""Tests for the RAG chain: formatting, prompt, and full chain."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from langchain_core.documents import Document

from oracle_rag.rag import RAG_PROMPT, format_docs, format_sources, run_rag
from oracle_rag.llm import get_chat_model


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

    from oracle_rag.indexing import index_pdf
    from oracle_rag.embeddings import get_embedding_model

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
