"""Tests for indexing PDFs into Chroma."""

from __future__ import annotations

from pathlib import Path

import pytest

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from oracle_rag.indexing import IndexResult, index_pdf, query_index
from oracle_rag.vectorstore import get_chroma_store


class _MockEmbeddings(Embeddings):
    """Returns fixed-dim vectors (1536) for testing without API key."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 1536 for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.1] * 1536


def test_index_pdf_smoke(tmp_path: Path) -> None:
    """Index a sample PDF into a temp Chroma dir and verify chunks are stored."""
    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present; skipping indexing test")

    persist_dir = tmp_path / "chroma_idx"
    result = index_pdf(
        sample_pdf,
        persist_directory=str(persist_dir),
        collection_name="test_index",
        embedding=_MockEmbeddings(),
    )

    assert isinstance(result, IndexResult)
    assert result.total_pages > 0
    assert result.total_chunks > 0
    assert result.persist_directory == persist_dir.resolve()

    # Re-open the store and ensure we can retrieve something back.
    store = get_chroma_store(
        persist_directory=str(persist_dir),
        collection_name="test_index",
        embedding=_MockEmbeddings(),
    )
    docs = store.similarity_search("test", k=2)
    assert len(docs) > 0
    assert isinstance(docs[0], Document)


def test_query_index_uses_existing_store(tmp_path: Path) -> None:
    """query_index returns results from an already-indexed Chroma store."""
    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present; skipping indexing test")

    persist_dir = tmp_path / "chroma_idx"
    result = index_pdf(
        sample_pdf,
        persist_directory=str(persist_dir),
        collection_name="test_query_index",
        embedding=_MockEmbeddings(),
    )

    docs = query_index(
        "test",
        k=2,
        persist_directory=result.persist_directory,
        collection_name=result.collection_name,
        embedding=_MockEmbeddings(),
    )
    assert len(docs) > 0
    assert isinstance(docs[0], Document)

