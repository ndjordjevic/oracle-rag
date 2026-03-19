"""Unit tests for plaintext indexer (index_plaintext)."""

from __future__ import annotations

from pathlib import Path

from pinrag.indexing.plaintext_indexer import (
    PlaintextIndexResult,
    index_plaintext,
)
from tests.helpers.embeddings import MockEmbeddings1536


def test_index_plaintext_smoke(tmp_path: Path) -> None:
    """Index small .txt; verify result and Chroma contents."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text(
        "Hello world. This is a test document for indexing.", encoding="utf-8"
    )
    persist = str(tmp_path / "chroma")

    result = index_plaintext(
        txt_file,
        persist_directory=persist,
        collection_name="test_plain",
        embedding=MockEmbeddings1536(),
    )

    assert isinstance(result, PlaintextIndexResult)
    assert result.source_path == txt_file.resolve()
    assert result.document_id == "notes.txt"
    assert result.total_chunks > 0
    assert result.collection_name == "test_plain"

    from pinrag.vectorstore import get_chroma_store

    store = get_chroma_store(
        persist_directory=persist,
        collection_name="test_plain",
        embedding=MockEmbeddings1536(),
    )
    docs = store.similarity_search("Hello", k=5)
    assert len(docs) > 0
    assert docs[0].metadata.get("document_type") == "plaintext"
    assert docs[0].metadata.get("document_id") == "notes.txt"


def test_index_plaintext_replaces_on_reindex(tmp_path: Path) -> None:
    """Indexing same file twice replaces chunks (no duplicates)."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Hello world. This is a test.", encoding="utf-8")
    persist = str(tmp_path / "chroma")
    emb = MockEmbeddings1536()

    r1 = index_plaintext(
        txt_file,
        persist_directory=persist,
        collection_name="test_coll",
        embedding=emb,
    )
    r2 = index_plaintext(
        txt_file,
        persist_directory=persist,
        collection_name="test_coll",
        embedding=emb,
    )

    assert r2.total_chunks == r1.total_chunks


def test_index_plaintext_file_over_cap_clears_old(tmp_path: Path) -> None:
    """File over cap returns 0 chunks and clears existing chunks for document_id."""
    txt_file = tmp_path / "large.txt"
    txt_file.write_text("x" * 2000, encoding="utf-8")
    persist = str(tmp_path / "chroma")
    emb = MockEmbeddings1536()

    # First index with small content
    small_file = tmp_path / "small.txt"
    small_file.write_text("Hello world", encoding="utf-8")
    index_plaintext(
        small_file,
        persist_directory=persist,
        collection_name="test_cap",
        embedding=emb,
        document_id="large.txt",
    )

    # Now index large.txt (over cap) - should clear old chunks for document_id
    result = index_plaintext(
        txt_file,
        persist_directory=persist,
        collection_name="test_cap",
        embedding=emb,
        max_file_bytes=500,
    )

    assert result.total_chunks == 0
    assert result.document_id == "large.txt"

    from pinrag.vectorstore import get_chroma_store

    store = get_chroma_store(
        persist_directory=persist,
        collection_name="test_cap",
        embedding=MockEmbeddings1536(),
    )
    docs = store.get(where={"document_id": "large.txt"})
    assert docs is not None
    assert len(docs.get("ids", [])) == 0


def test_index_plaintext_metadata_fields(tmp_path: Path) -> None:
    """Indexed chunks have expected metadata fields."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Hello world. Test content.", encoding="utf-8")
    persist = str(tmp_path / "chroma")

    index_plaintext(
        txt_file,
        persist_directory=persist,
        collection_name="test_meta",
        embedding=MockEmbeddings1536(),
    )

    from pinrag.vectorstore import get_chroma_store

    store = get_chroma_store(
        persist_directory=persist,
        collection_name="test_meta",
        embedding=MockEmbeddings1536(),
    )
    docs = store.similarity_search("Hello", k=1)
    meta = docs[0].metadata
    assert meta["document_type"] == "plaintext"
    assert "upload_timestamp" in meta
    assert "doc_total_chunks" in meta
    assert "doc_bytes" in meta
    assert "source" in meta


def test_index_plaintext_with_tag(tmp_path: Path) -> None:
    """Tag is propagated to chunk metadata."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Hello world.", encoding="utf-8")
    persist = str(tmp_path / "chroma")

    index_plaintext(
        txt_file,
        persist_directory=persist,
        collection_name="test_tag",
        embedding=MockEmbeddings1536(),
        tag="NOTES",
    )

    from pinrag.vectorstore import get_chroma_store

    store = get_chroma_store(
        persist_directory=persist,
        collection_name="test_tag",
        embedding=MockEmbeddings1536(),
    )
    docs = store.similarity_search("Hello", k=5)
    assert all(d.metadata.get("tag") == "NOTES" for d in docs)
