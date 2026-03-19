"""Shared test doubles for embedding models."""

from __future__ import annotations

from langchain_core.embeddings import Embeddings


class MockEmbeddings1536(Embeddings):
    """Fixed 1536-dimensional vectors for tests (no API calls)."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one constant vector per input string."""
        return [[0.1] * 1536 for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        """Return a constant vector for the query."""
        return [0.1] * 1536
