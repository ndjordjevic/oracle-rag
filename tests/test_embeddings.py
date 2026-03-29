"""Tests for embedding client."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pinrag.chunking import chunk_documents
from pinrag.embeddings.openai_client import DEFAULT_MODEL, get_embedding_model
from pinrag.indexing.pdf_loader import load_pdf_as_documents


def test_get_embedding_model_returns_nomic_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_embedding_model returns a NomicEmbeddings instance."""
    monkeypatch.delenv("PINRAG_EMBEDDING_MODEL", raising=False)
    mock_emb = MagicMock()
    with patch("langchain_nomic.NomicEmbeddings", return_value=mock_emb):
        emb = get_embedding_model()
    assert emb is mock_emb


def test_get_embedding_model_uses_default_model_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """When PINRAG_EMBEDDING_MODEL is unset, NomicEmbeddings receives default id."""
    monkeypatch.delenv("PINRAG_EMBEDDING_MODEL", raising=False)
    with patch("langchain_nomic.NomicEmbeddings") as mock_cls:
        get_embedding_model()
    mock_cls.assert_called_once()
    call_kw = mock_cls.call_args[1]
    assert call_kw["model"] == DEFAULT_MODEL
    assert call_kw["inference_mode"] == "local"


def test_missing_langchain_nomic_raises_import_error() -> None:
    """If langchain_nomic is not importable, get_embedding_model raises ImportError."""
    with patch("pinrag.embeddings.openai_client.find_spec", return_value=None):
        with pytest.raises(ImportError, match="langchain-nomic"):
            get_embedding_model()


def test_embed_query_generates_vector_768(monkeypatch: pytest.MonkeyPatch) -> None:
    """embed_query returns a list of floats of expected dimension without loading weights."""
    monkeypatch.delenv("PINRAG_EMBEDDING_MODEL", raising=False)
    with patch("langchain_nomic.NomicEmbeddings") as mock_cls:
        instance = MagicMock()
        instance.embed_query = lambda _q: [0.0] * 768
        mock_cls.return_value = instance
        emb = get_embedding_model()
    result = emb.embed_query("test")
    assert isinstance(result, list)
    assert len(result) == 768
    assert all(isinstance(x, float) for x in result)


def test_embed_pdf_chunks_768(monkeypatch: pytest.MonkeyPatch, sample_pdf_path: Path) -> None:
    """Load a PDF, chunk it, and create mocked embeddings for a few chunks."""
    monkeypatch.delenv("PINRAG_EMBEDDING_MODEL", raising=False)
    with patch("langchain_nomic.NomicEmbeddings") as mock_cls:
        instance = MagicMock()
        instance.embed_documents = lambda texts: [[0.0] * 768 for _ in texts]
        mock_cls.return_value = instance
        result = load_pdf_as_documents(sample_pdf_path)
        chunks = chunk_documents(result.documents, chunk_size=400, chunk_overlap=50)
        assert len(chunks) >= 2

        texts = [c.page_content for c in chunks[:3]]
        emb = get_embedding_model()
        vectors = emb.embed_documents(texts)

    assert len(vectors) == len(texts)
    for v in vectors:
        assert isinstance(v, list)
        assert len(v) == 768
        assert all(isinstance(x, float) for x in v)
