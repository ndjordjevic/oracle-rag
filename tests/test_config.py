"""Tests for configuration (env vars)."""

from __future__ import annotations

import os

import pytest

from oracle_rag.config import get_chunk_overlap, get_chunk_size, get_collection_name


def test_get_chunk_size_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without env var, returns default 1000."""
    monkeypatch.delenv("ORACLE_RAG_CHUNK_SIZE", raising=False)
    assert get_chunk_size() == 1000


def test_get_chunk_size_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """With valid env var, returns parsed int."""
    monkeypatch.setenv("ORACLE_RAG_CHUNK_SIZE", "1500")
    assert get_chunk_size() == 1500


def test_get_chunk_size_invalid_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """With invalid env var, returns default."""
    monkeypatch.setenv("ORACLE_RAG_CHUNK_SIZE", "not_a_number")
    assert get_chunk_size() == 1000


def test_get_chunk_size_negative_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """With negative value, returns default."""
    monkeypatch.setenv("ORACLE_RAG_CHUNK_SIZE", "-1")
    assert get_chunk_size() == 1000


def test_get_chunk_overlap_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without env var, returns default 200."""
    monkeypatch.delenv("ORACLE_RAG_CHUNK_OVERLAP", raising=False)
    assert get_chunk_overlap() == 200


def test_get_chunk_overlap_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """With valid env var, returns parsed int."""
    monkeypatch.setenv("ORACLE_RAG_CHUNK_OVERLAP", "300")
    assert get_chunk_overlap() == 300


def test_get_chunk_overlap_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """Zero overlap is valid."""
    monkeypatch.setenv("ORACLE_RAG_CHUNK_OVERLAP", "0")
    assert get_chunk_overlap() == 0


def test_get_chunk_overlap_invalid_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """With invalid env var, returns default."""
    monkeypatch.setenv("ORACLE_RAG_CHUNK_OVERLAP", "abc")
    assert get_chunk_overlap() == 200


def test_get_collection_name_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """With ORACLE_RAG_COLLECTION_NAME set, returns that value."""
    monkeypatch.setenv("ORACLE_RAG_COLLECTION_NAME", "my_custom_collection")
    assert get_collection_name() == "my_custom_collection"


def test_get_collection_name_from_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without ORACLE_RAG_COLLECTION_NAME, returns oracle_rag_<provider>."""
    monkeypatch.delenv("ORACLE_RAG_COLLECTION_NAME", raising=False)
    monkeypatch.setenv("ORACLE_RAG_EMBEDDING_PROVIDER", "openai")
    assert get_collection_name() == "oracle_rag_openai"
    monkeypatch.setenv("ORACLE_RAG_EMBEDDING_PROVIDER", "cohere")
    assert get_collection_name() == "oracle_rag_cohere"
