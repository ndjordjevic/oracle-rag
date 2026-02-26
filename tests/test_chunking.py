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
        assert "section" in chunk.metadata
        assert chunk.metadata["file_name"] == sample_pdf.name
        assert chunk.metadata["document_id"] == sample_pdf.name
        assert chunk.metadata["chunk_index"] >= 0
        assert isinstance(chunk.metadata["section"], str)
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


def test_chunk_documents_section_metadata() -> None:
    """Chunks get explicit section labels when content has heading-like lines."""
    # First line is a heading (short, no trailing punctuation), second is paragraph
    doc = Document(
        page_content="Introduction\n\nThis is the first paragraph of the document.",
        metadata={"source": "/path/to/file.pdf", "file_name": "file.pdf", "page": 1, "total_pages": 1},
    )
    chunks = chunk_documents([doc], chunk_size=1000, chunk_overlap=0)
    assert len(chunks) >= 1
    assert chunks[0].metadata["section"] == "Introduction"

    # Multiple paragraphs: first chunk has heading, second has same section (carry-forward)
    doc2 = Document(
        page_content="Chapter One\n\nFirst paragraph.\n\nSecond paragraph here.",
        metadata={"source": "/path/to/file.pdf", "file_name": "file.pdf", "page": 1, "total_pages": 1},
    )
    chunks2 = chunk_documents([doc2], chunk_size=50, chunk_overlap=0)
    assert len(chunks2) >= 2
    assert chunks2[0].metadata["section"] == "Chapter One"
    assert chunks2[1].metadata["section"] == "Chapter One"

    # Paragraph with trailing punctuation is not a heading (no section until we see one)
    doc3 = Document(
        page_content="This is a sentence.\n\nMore content here.",
        metadata={"source": "/path/to/file.pdf", "file_name": "file.pdf", "page": 1, "total_pages": 1},
    )
    chunks3 = chunk_documents([doc3], chunk_size=1000, chunk_overlap=0)
    assert len(chunks3) >= 1
    assert chunks3[0].metadata["section"] == ""
