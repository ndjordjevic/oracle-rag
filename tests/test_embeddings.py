"""Tests for embedding client."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from langchain_openai import OpenAIEmbeddings

from oracle_rag.chunking import chunk_documents
from oracle_rag.embeddings.openai_client import DEFAULT_MODEL, get_embedding_model
from oracle_rag.pdf.pypdf_loader import load_pdf_as_documents


def test_get_embedding_model_returns_client() -> None:
    """get_embedding_model returns an OpenAIEmbeddings instance."""
    # May fail if OPENAI_API_KEY is missing (client validates on init in some versions)
    try:
        emb = get_embedding_model()
    except Exception:
        pytest.skip("OPENAI_API_KEY not set or invalid; skipping")
    assert isinstance(emb, OpenAIEmbeddings)
    assert emb.model == DEFAULT_MODEL


def test_embed_query_generates_vector() -> None:
    """embed_query returns a list of floats of expected dimension (1536 for text-embedding-3-small)."""
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set; skipping embedding API test")

    emb = get_embedding_model()
    result = emb.embed_query("test")
    assert isinstance(result, list)
    assert len(result) == 1536
    assert all(isinstance(x, float) for x in result)


def test_embed_pdf_chunks() -> None:
    """Load a PDF, chunk it, and create embeddings for a few chunks (pipeline smoke test)."""
    from dotenv import load_dotenv
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set; skipping embedding API test")

    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present; skipping embed-chunks test")

    result = load_pdf_as_documents(sample_pdf)
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
