"""Unit tests for MCP tool implementations (add_pdf, query_pdf, list_pdfs)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from oracle_rag.mcp.tools import add_pdf, add_pdfs, list_pdfs, query_pdf
from oracle_rag.mcp import server as mcp_server


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
    assert "document_details" in result
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
    assert result["document_details"] == {}


def test_list_pdfs_includes_document_details_when_present(tmp_path: Path) -> None:
    """list_pdfs returns document_details (upload_timestamp, pages, bytes, chunks, tag) when chunks have them."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    mock_store = MagicMock()
    mock_store.get.return_value = {
        "metadatas": [
            {"document_id": "doc.pdf", "upload_timestamp": "2025-01-15T12:00:00Z", "doc_pages": 56, "doc_bytes": 12345, "doc_total_chunks": 224, "tag": "amiga"},
            {"document_id": "doc.pdf", "upload_timestamp": "2025-01-15T12:00:00Z", "doc_pages": 56, "doc_bytes": 12345, "doc_total_chunks": 224, "tag": "amiga"},
        ]
    }

    with patch("oracle_rag.mcp.tools.get_chroma_store", return_value=mock_store):
        result = list_pdfs(persist_dir=str(tmp_path), collection="test_coll")

    assert result["documents"] == ["doc.pdf"]
    assert result["document_details"]["doc.pdf"] == {
        "upload_timestamp": "2025-01-15T12:00:00Z",
        "pages": 56,
        "bytes": 12345,
        "chunks": 224,
        "tag": "amiga",
    }


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


def test_add_pdf_pdf_loading_error_propagates(tmp_path: Path) -> None:
    """add_pdf propagates PDF loading / indexing errors (e.g. no text extracted)."""
    pdf_file = tmp_path / "bad.pdf"
    pdf_file.write_bytes(b"not a real pdf")
    with patch("oracle_rag.mcp.tools.get_embedding_model"):
        with patch("oracle_rag.mcp.tools.index_pdf", side_effect=ValueError("No text extracted")):
            with pytest.raises(ValueError, match="No text extracted"):
                add_pdf(
                    pdf_path=str(pdf_file),
                    persist_dir=str(tmp_path),
                    collection="test_coll",
                )


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

    with patch("oracle_rag.mcp.tools.index_pdf", return_value=fake_result) as mock_index:
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
    mock_index.assert_called_once_with(
        pdf_file,
        persist_directory=str(tmp_path),
        collection_name="test_coll",
        embedding=mock_index.call_args[1]["embedding"],
        tag=None,
    )


def test_add_pdf_with_tag_passes_tag_to_index(tmp_path: Path) -> None:
    """add_pdf passes tag to index_pdf when provided."""
    pdf_file = tmp_path / "sample.pdf"
    pdf_file.touch()
    fake_result = MagicMock()
    fake_result.source_path = pdf_file
    fake_result.total_pages = 5
    fake_result.total_chunks = 12
    fake_result.persist_directory = tmp_path / "chroma_db"
    fake_result.collection_name = "test_coll"

    with patch("oracle_rag.mcp.tools.index_pdf", return_value=fake_result) as mock_index:
        with patch("oracle_rag.mcp.tools.get_embedding_model"):
            add_pdf(
                pdf_path=str(pdf_file),
                persist_dir=str(tmp_path),
                collection="test_coll",
                tag="amiga",
            )

    mock_index.assert_called_once()
    assert mock_index.call_args[1]["tag"] == "amiga"


def test_add_pdfs_tags_length_mismatch_raises() -> None:
    """add_pdfs raises when tags length does not match pdf_paths."""
    with pytest.raises(ValueError, match="tags must have same length"):
        add_pdfs(pdf_paths=["a.pdf", "b.pdf"], tags=["amiga"])


def test_add_pdfs_empty_paths_raises() -> None:
    """add_pdfs raises ValueError when path list is empty."""
    with pytest.raises(ValueError, match="pdf_paths cannot be empty"):
        add_pdfs(pdf_paths=[])


def test_add_pdfs_partial_success(tmp_path: Path) -> None:
    """add_pdfs indexes valid files and reports failures per file."""
    good_pdf = tmp_path / "good.pdf"
    bad_ext = tmp_path / "bad.txt"
    good_pdf.touch()
    bad_ext.touch()

    fake_result = MagicMock()
    fake_result.source_path = good_pdf
    fake_result.total_pages = 3
    fake_result.total_chunks = 7

    with patch("oracle_rag.mcp.tools.index_pdf", return_value=fake_result) as mock_index:
        with patch("oracle_rag.mcp.tools.get_embedding_model"):
            result = add_pdfs(
                pdf_paths=[str(good_pdf), str(bad_ext), str(tmp_path / "missing.pdf")],
                persist_dir=str(tmp_path),
                collection="test_coll",
            )

    assert result["total_indexed"] == 1
    assert result["total_failed"] == 2
    assert result["collection_name"] == "test_coll"
    assert len(result["indexed"]) == 1
    assert result["indexed"][0]["source_path"] == str(good_pdf)
    assert len(result["failed"]) == 2
    mock_index.assert_called_once()


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


def test_query_pdf_chain_error_propagates(tmp_path: Path) -> None:
    """query_pdf propagates retrieval/LLM errors from run_rag."""
    (tmp_path / "chroma_db").mkdir(parents=True, exist_ok=True)

    with patch("oracle_rag.mcp.tools.get_embedding_model"):
        with patch("oracle_rag.mcp.tools.get_chat_model"):
            with patch(
                "oracle_rag.mcp.tools.run_rag",
                side_effect=RuntimeError("OpenAI API rate limit"),
            ):
                with pytest.raises(RuntimeError, match="OpenAI API rate limit"):
                    query_pdf(
                        query="test",
                        persist_dir=str(tmp_path),
                        collection="test_coll",
                    )


def test_query_pdf_success(tmp_path: Path) -> None:
    """query_pdf returns answer and sources when run_rag succeeds."""
    from oracle_rag.rag import RAGResult

    (tmp_path / "chroma_db").mkdir(parents=True, exist_ok=True)
    mock_run_rag = MagicMock(
        return_value=RAGResult(
            answer="The answer is 42.",
            sources=[
                {"document_id": "doc.pdf", "page": 1},
                {"document_id": "doc.pdf", "page": 2},
            ],
        )
    )

    with patch("oracle_rag.mcp.tools.get_embedding_model"):
        with patch("oracle_rag.mcp.tools.get_chat_model"):
            with patch("oracle_rag.mcp.tools.run_rag", mock_run_rag):
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
    mock_run_rag.assert_called_once()
    call_args, call_kwargs = mock_run_rag.call_args
    assert call_args[0] == "What is the answer?"
    assert call_kwargs["k"] == 3
    assert call_kwargs.get("document_id") is None


def test_query_pdf_page_range_validation(tmp_path: Path) -> None:
    """query_pdf raises when page_min or page_max is provided without the other."""
    (tmp_path / "chroma_db").mkdir(parents=True, exist_ok=True)
    with patch("oracle_rag.mcp.tools.get_embedding_model"):
        with patch("oracle_rag.mcp.tools.get_chat_model"):
            with pytest.raises(ValueError, match="page_min and page_max must be provided together"):
                query_pdf(
                    query="test",
                    persist_dir=str(tmp_path),
                    page_min=1,
                )
            with pytest.raises(ValueError, match="page_min and page_max must be provided together"):
                query_pdf(
                    query="test",
                    persist_dir=str(tmp_path),
                    page_max=10,
                )
            with pytest.raises(ValueError, match="page_min must be <= page_max"):
                query_pdf(
                    query="test",
                    persist_dir=str(tmp_path),
                    page_min=10,
                    page_max=1,
                )


def test_query_pdf_with_page_range(tmp_path: Path) -> None:
    """query_pdf passes page_min and page_max to run_rag when provided."""
    from oracle_rag.rag import RAGResult

    (tmp_path / "chroma_db").mkdir(parents=True, exist_ok=True)
    mock_run_rag = MagicMock(
        return_value=RAGResult(
            answer="Page 16 content.",
            sources=[{"document_id": "pico.pdf", "page": 16}],
        )
    )

    with patch("oracle_rag.mcp.tools.get_embedding_model"):
        with patch("oracle_rag.mcp.tools.get_chat_model"):
            with patch("oracle_rag.mcp.tools.run_rag", mock_run_rag):
                query_pdf(
                    query="OpenOCD?",
                    k=3,
                    persist_dir=str(tmp_path),
                    collection="test_coll",
                    document_id="pico.pdf",
                    page_min=16,
                    page_max=16,
                )

    mock_run_rag.assert_called_once()
    assert mock_run_rag.call_args[1]["page_min"] == 16
    assert mock_run_rag.call_args[1]["page_max"] == 16


def test_query_pdf_with_tag_filter(tmp_path: Path) -> None:
    """query_pdf passes tag to run_rag when provided."""
    from oracle_rag.rag import RAGResult

    (tmp_path / "chroma_db").mkdir(parents=True, exist_ok=True)
    mock_run_rag = MagicMock(
        return_value=RAGResult(
            answer="From PI_PICO docs.",
            sources=[{"document_id": "pico.pdf", "page": 1}],
        )
    )

    with patch("oracle_rag.mcp.tools.get_embedding_model"):
        with patch("oracle_rag.mcp.tools.get_chat_model"):
            with patch("oracle_rag.mcp.tools.run_rag", mock_run_rag):
                query_pdf(
                    query="GPIO?",
                    k=3,
                    persist_dir=str(tmp_path),
                    collection="test_coll",
                    tag="PI_PICO",
                )

    mock_run_rag.assert_called_once()
    assert mock_run_rag.call_args[1]["tag"] == "PI_PICO"


def test_query_pdf_with_document_id_filter(tmp_path: Path) -> None:
    """query_pdf passes document_id to run_rag when provided."""
    from oracle_rag.rag import RAGResult

    (tmp_path / "chroma_db").mkdir(parents=True, exist_ok=True)
    mock_run_rag = MagicMock(
        return_value=RAGResult(
            answer="Filtered answer.",
            sources=[{"document_id": "pico.pdf", "page": 1}],
        )
    )

    with patch("oracle_rag.mcp.tools.get_embedding_model"):
        with patch("oracle_rag.mcp.tools.get_chat_model"):
            with patch("oracle_rag.mcp.tools.run_rag", mock_run_rag):
                query_pdf(
                    query="GPIO?",
                    k=3,
                    persist_dir=str(tmp_path),
                    collection="test_coll",
                    document_id="RP-008276-DS-1-getting-started-with-pico.pdf",
                )

    mock_run_rag.assert_called_once()
    assert mock_run_rag.call_args[1]["document_id"] == "RP-008276-DS-1-getting-started-with-pico.pdf"


# --- Error handling: propagate + log ---


def test_server_tool_logs_on_failure() -> None:
    """When a tool raises, the server decorator logs the exception then re-raises."""
    mock_log = MagicMock()
    with patch.object(mcp_server, "_log", mock_log):
        with pytest.raises(ValueError, match="Query cannot be empty"):
            mcp_server.query_pdf_tool(query="")
    mock_log.exception.assert_called_once()
