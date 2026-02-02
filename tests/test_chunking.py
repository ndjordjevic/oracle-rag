"""Tests for chunking splitter."""

from __future__ import annotations

from pathlib import Path

import pytest

from langchain_core.documents import Document

from oracle_rag.chunking.splitter import chunk_documents
from oracle_rag.pdf.pypdf_loader import load_pdf_as_documents


def test_chunk_documents_empty() -> None:
    assert chunk_documents([]) == []


def test_chunk_documents_preserves_metadata() -> None:
    """Chunks keep source metadata and get chunk_index and document_id."""
    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present; skipping chunking test")

    result = load_pdf_as_documents(sample_pdf)
    docs = result.documents
    chunks = chunk_documents(docs, chunk_size=500, chunk_overlap=50)

    assert len(chunks) >= len(docs)
    for chunk in chunks:
        assert "page" in chunk.metadata
        assert "file_name" in chunk.metadata
        assert "document_id" in chunk.metadata
        assert "chunk_index" in chunk.metadata
        assert chunk.metadata["file_name"] == sample_pdf.name
        assert chunk.metadata["document_id"] == sample_pdf.name
        assert chunk.metadata["chunk_index"] >= 0
        assert chunk.page_content.strip()


def test_chunk_documents_single_short_doc() -> None:
    """One short document becomes one chunk with chunk_index 0."""
    doc = Document(
        page_content="Short text.",
        metadata={"source": "/path/to/file.pdf", "file_name": "file.pdf", "page": 1, "total_pages": 1},
    )
    chunks = chunk_documents([doc], chunk_size=1000, chunk_overlap=0)
    assert len(chunks) == 1
    assert chunks[0].metadata["chunk_index"] == 0
    assert chunks[0].metadata["document_id"] == "file.pdf"
    assert chunks[0].metadata["page"] == 1
    assert chunks[0].page_content == "Short text."


def test_chunk_documents_long_doc_splits() -> None:
    """Long content is split into multiple chunks with ascending chunk_index."""
    long_text = "A. " + ("word " * 300)
    doc = Document(
        page_content=long_text,
        metadata={"source": "/path/to/file.pdf", "file_name": "file.pdf", "page": 1, "total_pages": 1},
    )
    chunks = chunk_documents([doc], chunk_size=200, chunk_overlap=20)
    assert len(chunks) > 1
    for i, chunk in enumerate(chunks):
        assert chunk.metadata["chunk_index"] == i
        assert chunk.metadata["document_id"] == "file.pdf"
    combined_len = sum(len(c.page_content) for c in chunks)
    assert combined_len >= len(long_text) - 100
