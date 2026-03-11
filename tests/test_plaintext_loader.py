"""Unit tests for plaintext loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from pinrag.indexing.plaintext_loader import (
    PlaintextLoadResult,
    load_plaintext_as_documents,
)


def test_load_plaintext_missing_file() -> None:
    """load_plaintext_as_documents raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Plain text file not found"):
        load_plaintext_as_documents("does-not-exist.txt")


def test_load_plaintext_valid(tmp_path: Path) -> None:
    """Load valid .txt returns one Document with content and metadata."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Hello world.\nThis is a test.\n", encoding="utf-8")

    result = load_plaintext_as_documents(txt_file)

    assert isinstance(result, PlaintextLoadResult)
    assert result.source_path == txt_file.resolve()
    assert len(result.documents) == 1
    assert result.total_chars == 29  # "Hello world.\nThis is a test.\n"
    doc = result.documents[0]
    assert doc.page_content == "Hello world.\nThis is a test.\n"
    assert doc.metadata["document_id"] == "notes.txt"
    assert doc.metadata["source"] == str(txt_file.resolve())


def test_load_plaintext_file_too_large(tmp_path: Path) -> None:
    """File exceeding max_file_bytes returns empty documents."""
    txt_file = tmp_path / "large.txt"
    content = "x" * 1000
    txt_file.write_text(content, encoding="utf-8")

    result = load_plaintext_as_documents(txt_file, max_file_bytes=500)

    assert result.source_path == txt_file.resolve()
    assert result.documents == []
    assert result.total_chars == 0


def test_load_plaintext_file_at_limit(tmp_path: Path) -> None:
    """File exactly at max_file_bytes is loaded."""
    txt_file = tmp_path / "exact.txt"
    content = "a" * 100
    txt_file.write_text(content, encoding="utf-8")

    result = load_plaintext_as_documents(txt_file, max_file_bytes=100)

    assert len(result.documents) == 1
    assert result.total_chars == 100


def test_load_plaintext_document_id_override(tmp_path: Path) -> None:
    """document_id override is used in metadata."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Content", encoding="utf-8")

    result = load_plaintext_as_documents(txt_file, document_id="custom-id")

    assert result.documents[0].metadata["document_id"] == "custom-id"


def test_load_plaintext_encoding_fallback(tmp_path: Path) -> None:
    """Invalid UTF-8 bytes are replaced (errors='replace')."""
    txt_file = tmp_path / "bad_encoding.txt"
    txt_file.write_bytes(b"Hello \xff\xfe world")

    result = load_plaintext_as_documents(txt_file)

    assert len(result.documents) == 1
    assert "Hello" in result.documents[0].page_content
    assert "world" in result.documents[0].page_content
