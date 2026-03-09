"""Tests for structure-aware chunking config."""

from __future__ import annotations

import pytest

from oracle_rag.config import get_structure_aware_chunking


def test_get_structure_aware_chunking_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ORACLE_RAG_STRUCTURE_AWARE_CHUNKING", raising=False)
    assert get_structure_aware_chunking() is True


def test_get_structure_aware_chunking_true_values(monkeypatch: pytest.MonkeyPatch) -> None:
    for val in ("1", "true", "True", "yes", "YES", "on", "ON"):
        monkeypatch.setenv("ORACLE_RAG_STRUCTURE_AWARE_CHUNKING", val)
        assert get_structure_aware_chunking() is True


def test_get_structure_aware_chunking_false_values(monkeypatch: pytest.MonkeyPatch) -> None:
    for val in ("0", "false", "False", "no", "off"):
        monkeypatch.setenv("ORACLE_RAG_STRUCTURE_AWARE_CHUNKING", val)
        assert get_structure_aware_chunking() is False
