"""Tests for configuration (env vars)."""

from __future__ import annotations

import os

import pytest

from oracle_rag.config import (
    get_chunk_overlap,
    get_chunk_size,
    get_collection_name,
    get_rerank_retrieve_k,
    get_rerank_top_n,
    get_use_rerank,
)


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


def test_get_collection_name_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without ORACLE_RAG_COLLECTION_NAME, returns oracle_rag."""
    monkeypatch.delenv("ORACLE_RAG_COLLECTION_NAME", raising=False)
    assert get_collection_name() == "oracle_rag"


# Re-ranking config
def test_get_use_rerank_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without env var, returns False."""
    monkeypatch.delenv("ORACLE_RAG_USE_RERANK", raising=False)
    assert get_use_rerank() is False


def test_get_use_rerank_true_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """With 1, true, yes, on (case-insensitive), returns True."""
    for val in ("1", "true", "True", "yes", "YES", "on", "ON"):
        monkeypatch.setenv("ORACLE_RAG_USE_RERANK", val)
        assert get_use_rerank() is True


def test_get_use_rerank_false_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """With 0, false, no, off, returns False."""
    for val in ("0", "false", "no", "off", ""):
        monkeypatch.setenv("ORACLE_RAG_USE_RERANK", val)
        assert get_use_rerank() is False


def test_get_rerank_retrieve_k_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without env var, falls back to get_retrieve_k() (default 20)."""
    monkeypatch.delenv("ORACLE_RAG_RETRIEVE_K", raising=False)
    monkeypatch.delenv("ORACLE_RAG_RERANK_RETRIEVE_K", raising=False)
    assert get_rerank_retrieve_k() == 20


def test_get_rerank_retrieve_k_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """With valid env var, returns parsed int."""
    monkeypatch.setenv("ORACLE_RAG_RERANK_RETRIEVE_K", "20")
    assert get_rerank_retrieve_k() == 20


def test_get_rerank_retrieve_k_invalid_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """With invalid env var, falls back to get_retrieve_k() (default 20)."""
    monkeypatch.delenv("ORACLE_RAG_RETRIEVE_K", raising=False)
    monkeypatch.setenv("ORACLE_RAG_RERANK_RETRIEVE_K", "x")
    assert get_rerank_retrieve_k() == 20


def test_get_rerank_top_n_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without env var, returns 10."""
    monkeypatch.delenv("ORACLE_RAG_RERANK_TOP_N", raising=False)
    assert get_rerank_top_n() == 10


def test_get_rerank_top_n_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """With valid env var, returns parsed int."""
    monkeypatch.setenv("ORACLE_RAG_RERANK_TOP_N", "3")
    assert get_rerank_top_n() == 3
