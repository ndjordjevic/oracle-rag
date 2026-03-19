"""Tests for embedding client."""

from __future__ import annotations

import builtins
import sys
from pathlib import Path

import pytest
from langchain_openai import OpenAIEmbeddings

from pinrag.chunking import chunk_documents
from pinrag.embeddings.openai_client import DEFAULT_MODEL, get_embedding_model
from pinrag.pdf.pypdf_loader import load_pdf_as_documents


def test_get_embedding_model_returns_client(monkeypatch) -> None:
    """get_embedding_model returns an OpenAIEmbeddings instance."""
    monkeypatch.setenv("PINRAG_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    emb = get_embedding_model()
    assert isinstance(emb, OpenAIEmbeddings)
    assert emb.model == DEFAULT_MODEL


def test_openai_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PINRAG_EMBEDDING_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        get_embedding_model()


def test_openai_explicit_api_key_skips_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PINRAG_EMBEDDING_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    emb = get_embedding_model(api_key="sk-from-arg")
    assert isinstance(emb, OpenAIEmbeddings)


def test_cohere_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("langchain_cohere")
    monkeypatch.setenv("PINRAG_EMBEDDING_PROVIDER", "cohere")
    monkeypatch.delenv("COHERE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="COHERE_API_KEY"):
        get_embedding_model()


def test_cohere_requires_langchain_cohere(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PINRAG_EMBEDDING_PROVIDER", "cohere")
    monkeypatch.delitem(sys.modules, "langchain_cohere", raising=False)
    real_import = builtins.__import__

    def _import(name: str, *args: object, **kwargs: object) -> object:
        if name == "langchain_cohere":
            raise ImportError("simulated missing package")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _import)
    with pytest.raises(ImportError, match="langchain-cohere"):
        get_embedding_model()


def test_embed_query_generates_vector(monkeypatch) -> None:
    """embed_query returns a list of floats of expected dimension without API calls."""
    monkeypatch.setenv("PINRAG_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setattr(
        OpenAIEmbeddings, "embed_query", lambda _self, _query: [0.0] * 1536
    )
    emb = get_embedding_model()
    result = emb.embed_query("test")
    assert isinstance(result, list)
    assert len(result) == 1536
    assert all(isinstance(x, float) for x in result)


def test_embed_pdf_chunks(monkeypatch, sample_pdf_path: Path) -> None:
    """Load a PDF, chunk it, and create mocked embeddings for a few chunks."""
    monkeypatch.setenv("PINRAG_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setattr(
        OpenAIEmbeddings,
        "embed_documents",
        lambda _self, texts: [[0.0] * 1536 for _ in texts],
    )
    result = load_pdf_as_documents(sample_pdf_path)
    chunks = chunk_documents(result.documents, chunk_size=400, chunk_overlap=50)
    assert len(chunks) >= 2

    # Embed first 3 chunks
    texts = [c.page_content for c in chunks[:3]]
    emb = get_embedding_model()
    vectors = emb.embed_documents(texts)

    assert len(vectors) == len(texts)
    for v in vectors:
        assert isinstance(v, list)
        assert len(v) == 1536
        assert all(isinstance(x, float) for x in v)
