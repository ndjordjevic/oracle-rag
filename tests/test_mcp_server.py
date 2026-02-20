"""Unit tests for MCP tool implementations (add_pdf, query_pdf, list_pdfs)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from oracle_rag.mcp.tools import add_pdf, list_pdfs, query_pdf


# --- list_pdfs ---


def test_list_pdfs_empty_collection_raises() -> None:
    """list_pdfs raises ValueError when collection is empty."""
    with pytest.raises(ValueError, match="collection cannot be empty"):
        list_pdfs(collection="")
    with pytest.raises(ValueError, match="collection cannot be empty"):
        list_pdfs(collection="   ")


def test_list_pdfs_missing_persist_dir_returns_empty() -> None:
    """list_pdfs returns empty documents when persist dir does not exist."""
    result = list_pdfs(persist_dir="/nonexistent/path/xyz", collection="test_coll")
    assert result["documents"] == []
    assert result["total_chunks"] == 0
    assert result["collection_name"] == "test_coll"
    assert "persist_directory" in result


def test_list_pdfs_returns_documents_from_store(tmp_path: Path) -> None:
    """list_pdfs returns unique document IDs and total_chunks from Chroma."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    mock_store = MagicMock()
    mock_store.get.return_value = {
        "metadatas": [
            {"file_name": "a.pdf", "page": 1},
            {"file_name": "a.pdf", "page": 2},
            {"document_id": "b.pdf", "page": 1},
        ]
    }

    with patch("oracle_rag.mcp.tools.get_chroma_store", return_value=mock_store):
        result = list_pdfs(persist_dir=str(tmp_path), collection="test_coll")

    assert result["documents"] == ["a.pdf", "b.pdf"]
    assert result["total_chunks"] == 3
    assert result["collection_name"] == "test_coll"
    mock_store.get.assert_called_once_with(include=["metadatas"])


def test_list_pdfs_handles_empty_metadatas(tmp_path: Path) -> None:
    """list_pdfs returns empty list when store has no chunks."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    mock_store = MagicMock()
    mock_store.get.return_value = {"metadatas": []}

    with patch("oracle_rag.mcp.tools.get_chroma_store", return_value=mock_store):
        result = list_pdfs(persist_dir=str(tmp_path), collection="test_coll")

    assert result["documents"] == []
    assert result["total_chunks"] == 0


# --- add_pdf ---


def test_add_pdf_empty_path_raises() -> None:
    """add_pdf raises ValueError when pdf_path is empty."""
    with pytest.raises(ValueError, match="pdf_path cannot be empty"):
        add_pdf(pdf_path="")
    with pytest.raises(ValueError, match="pdf_path cannot be empty"):
        add_pdf(pdf_path="   ")


def test_add_pdf_empty_collection_raises(tmp_path: Path) -> None:
    """add_pdf raises ValueError when collection is empty."""
    pdf_file = tmp_path / "dummy.pdf"
    pdf_file.touch()
    with pytest.raises(ValueError, match="collection cannot be empty"):
        add_pdf(pdf_path=str(pdf_file), collection="")


def test_add_pdf_file_not_found_raises() -> None:
    """add_pdf raises FileNotFoundError when the file does not exist."""
    with pytest.raises(FileNotFoundError, match="PDF file not found"):
        add_pdf(pdf_path="/nonexistent/file.pdf")


def test_add_pdf_not_pdf_raises(tmp_path: Path) -> None:
    """add_pdf raises ValueError when file is not a .pdf."""
    txt_file = tmp_path / "doc.txt"
    txt_file.touch()
    with pytest.raises(ValueError, match="File is not a PDF"):
        add_pdf(pdf_path=str(txt_file))


def test_add_pdf_success(tmp_path: Path) -> None:
    """add_pdf returns indexing result when PDF exists and index_pdf succeeds."""
    pdf_file = tmp_path / "sample.pdf"
    pdf_file.touch()
    fake_result = MagicMock()
    fake_result.source_path = pdf_file
    fake_result.total_pages = 5
    fake_result.total_chunks = 12
    fake_result.persist_directory = tmp_path / "chroma_db"
    fake_result.collection_name = "test_coll"

    with patch("oracle_rag.mcp.tools.index_pdf", return_value=fake_result):
        with patch("oracle_rag.mcp.tools.get_embedding_model"):
            result = add_pdf(
                pdf_path=str(pdf_file),
                persist_dir=str(tmp_path),
                collection="test_coll",
            )

    assert result["source_path"] == str(pdf_file)
    assert result["total_pages"] == 5
    assert result["total_chunks"] == 12
    assert result["collection_name"] == "test_coll"
    assert "persist_directory" in result


# --- query_pdf ---


def test_query_pdf_empty_query_raises() -> None:
    """query_pdf raises ValueError when query is empty."""
    with pytest.raises(ValueError, match="Query cannot be empty"):
        query_pdf(query="")
    with pytest.raises(ValueError, match="Query cannot be empty"):
        query_pdf(query="   ")


def test_query_pdf_invalid_k_raises() -> None:
    """query_pdf raises ValueError when k is out of range or not an int."""
    with pytest.raises(ValueError, match="k must be an integer"):
        query_pdf(query="test", k=0)
    with pytest.raises(ValueError, match="k must be an integer"):
        query_pdf(query="test", k=101)


def test_query_pdf_empty_collection_raises(tmp_path: Path) -> None:
    """query_pdf raises ValueError when collection is empty."""
    (tmp_path / "chroma_db").mkdir(parents=True, exist_ok=True)
    with pytest.raises(ValueError, match="collection cannot be empty"):
        query_pdf(query="test", persist_dir=str(tmp_path), collection="")


def test_query_pdf_missing_persist_dir_raises() -> None:
    """query_pdf raises FileNotFoundError when persist dir does not exist."""
    with pytest.raises(FileNotFoundError, match="Persistence directory does not exist"):
        query_pdf(query="test", persist_dir="/nonexistent/chroma_db")


def test_query_pdf_success(tmp_path: Path) -> None:
    """query_pdf returns answer and sources when chain runs successfully."""
    (tmp_path / "chroma_db").mkdir(parents=True, exist_ok=True)
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {
        "answer": "The answer is 42.",
        "sources": [
            {"document_id": "doc.pdf", "page": 1},
            {"document_id": "doc.pdf", "page": 2},
        ],
    }

    with patch("oracle_rag.mcp.tools.get_embedding_model"):
        with patch("oracle_rag.mcp.tools.get_chat_model"):
            with patch("oracle_rag.mcp.tools.get_rag_chain", return_value=mock_chain):
                result = query_pdf(
                    query="What is the answer?",
                    k=3,
                    persist_dir=str(tmp_path),
                    collection="test_coll",
                )

    assert result["answer"] == "The answer is 42."
    assert len(result["sources"]) == 2
    assert result["sources"][0] == {"document_id": "doc.pdf", "page": 1}
    assert result["sources"][1] == {"document_id": "doc.pdf", "page": 2}
    mock_chain.invoke.assert_called_once_with({"query": "What is the answer?", "k": 3})
