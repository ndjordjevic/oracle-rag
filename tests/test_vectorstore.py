"""Tests for Chroma vector store."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from oracle_rag.vectorstore.chroma_client import (
    DEFAULT_COLLECTION_NAME,
    get_chroma_store,
)


class _MockEmbeddings(Embeddings):
    """Returns fixed-dim vectors (1536) for testing without API key."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 1536 for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.1] * 1536


def test_get_chroma_store_returns_chroma(tmp_path: Path) -> None:
    """get_chroma_store returns a Chroma instance with given persist dir and collection."""
    store = get_chroma_store(
        persist_directory=str(tmp_path),
        collection_name="test_collection",
        embedding=_MockEmbeddings(),
    )
    assert isinstance(store, Chroma)
    assert store._collection.name == "test_collection"


def test_get_chroma_store_creates_persist_dir(tmp_path: Path) -> None:
    """get_chroma_store creates the persist directory if it does not exist."""
    persist_dir = tmp_path / "new_chroma_dir"
    assert not persist_dir.exists()
    get_chroma_store(
        persist_directory=str(persist_dir),
        embedding=_MockEmbeddings(),
    )
    assert persist_dir.exists()
    assert persist_dir.is_dir()


def test_chroma_add_documents_and_similarity_search(tmp_path: Path) -> None:
    """Add documents to Chroma and run similarity_search; returns matching docs."""
    store = get_chroma_store(
        persist_directory=str(tmp_path),
        collection_name="test_add_search",
        embedding=_MockEmbeddings(),
    )
    docs = [
        Document(page_content="The Amiga had custom chips.", metadata={"page": 1}),
        Document(page_content="Chip memory is used by the processor.", metadata={"page": 2}),
    ]
    store.add_documents(docs)
    results = store.similarity_search("Amiga chips", k=2)
    assert len(results) >= 1
    assert any("Amiga" in d.page_content or "chip" in d.page_content.lower() for d in results)


def test_chroma_add_and_search_with_real_embedding(tmp_path: Path) -> None:
    """Add documents and similarity_search using real OpenAI embeddings (skip if no API key)."""
    from dotenv import load_dotenv
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set; skipping real-embedding Chroma test")

    from oracle_rag.embeddings import get_embedding_model
    store = get_chroma_store(
        persist_directory=str(tmp_path),
        collection_name="test_real_embed",
        embedding=get_embedding_model(),
    )
    docs = [
        Document(page_content="The MC68000 is a 16-bit processor.", metadata={"page": 1, "file_name": "doc.pdf"}),
    ]
    store.add_documents(docs)
    results = store.similarity_search("68000 processor", k=1)
    assert len(results) == 1
    assert "68000" in results[0].page_content
    assert results[0].metadata.get("page") == 1
