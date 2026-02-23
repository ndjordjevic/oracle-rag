"""Tests for configuration (env vars)."""

from __future__ import annotations

import os

import pytest

from oracle_rag.config import get_chunk_overlap, get_chunk_size


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
