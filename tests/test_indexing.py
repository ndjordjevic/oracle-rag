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
    meta = docs[0].metadata
    assert "upload_timestamp" in meta
    assert "doc_pages" in meta
    assert "doc_bytes" in meta
    assert "doc_total_chunks" in meta


def test_index_pdf_with_tag(tmp_path: Path) -> None:
    """Index with tag; chunks have tag in metadata."""
    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present; skipping indexing test")

    persist_dir = tmp_path / "chroma_idx"
    index_pdf(
        sample_pdf,
        persist_directory=str(persist_dir),
        collection_name="test_tag",
        embedding=_MockEmbeddings(),
        tag="amiga",
    )

    store = get_chroma_store(
        persist_directory=str(persist_dir),
        collection_name="test_tag",
        embedding=_MockEmbeddings(),
    )
    docs = store.similarity_search("test", k=2)
    assert len(docs) > 0
    assert docs[0].metadata.get("tag") == "amiga"


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


def test_index_pdf_replaces_duplicate(tmp_path: Path) -> None:
    """Indexing the same PDF twice replaces old chunks; no duplicates."""
    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present; skipping indexing test")

    persist_dir = tmp_path / "chroma_idx"
    coll = "test_replace"
    emb = _MockEmbeddings()

    result1 = index_pdf(
        sample_pdf,
        persist_directory=str(persist_dir),
        collection_name=coll,
        embedding=emb,
    )
    store = get_chroma_store(
        persist_directory=str(persist_dir),
        collection_name=coll,
        embedding=emb,
    )
    data1 = store._collection.get(include=[])
    count1 = len(data1.get("ids") or [])

    # Index same PDF again — should replace, not add
    result2 = index_pdf(
        sample_pdf,
        persist_directory=str(persist_dir),
        collection_name=coll,
        embedding=emb,
    )
    data2 = store._collection.get(include=[])
    count2 = len(data2.get("ids") or [])

    assert count2 == count1, "Re-indexing should replace chunks, not duplicate"
    assert result2.total_chunks == result1.total_chunks


def test_index_pdf_uses_config_chunk_size_from_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """index_pdf uses ORACLE_RAG_CHUNK_SIZE / ORACLE_RAG_CHUNK_OVERLAP when not passed."""
    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present; skipping indexing test")

    persist_dir = tmp_path / "chroma_idx"
    emb = _MockEmbeddings()

    # Default config (no env set) → default chunk size
    monkeypatch.delenv("ORACLE_RAG_CHUNK_SIZE", raising=False)
    monkeypatch.delenv("ORACLE_RAG_CHUNK_OVERLAP", raising=False)
    result_default = index_pdf(
        sample_pdf,
        persist_directory=str(persist_dir),
        collection_name="test_config_default",
        embedding=emb,
    )

    # Set env to smaller chunk size → index_pdf (without kwargs) should use it → more chunks
    monkeypatch.setenv("ORACLE_RAG_CHUNK_SIZE", "200")
    monkeypatch.setenv("ORACLE_RAG_CHUNK_OVERLAP", "0")
    result_from_env = index_pdf(
        sample_pdf,
        persist_directory=str(persist_dir),
        collection_name="test_config_env",
        embedding=emb,
    )
    assert result_from_env.total_chunks > result_default.total_chunks


def test_index_pdf_respects_chunk_size_override(tmp_path: Path) -> None:
    """index_pdf uses explicit chunk_size/chunk_overlap when passed."""
    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present; skipping indexing test")

    persist_dir = tmp_path / "chroma_idx"
    result_default = index_pdf(
        sample_pdf,
        persist_directory=str(persist_dir),
        collection_name="test_default",
        embedding=_MockEmbeddings(),
    )
    result_small = index_pdf(
        sample_pdf,
        persist_directory=str(persist_dir),
        collection_name="test_small",
        embedding=_MockEmbeddings(),
        chunk_size=200,
        chunk_overlap=0,
    )
    # Smaller chunks → more chunks for the same content
    assert result_small.total_chunks > result_default.total_chunks

