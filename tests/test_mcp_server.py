"""Unit tests for MCP tool implementations (add_file, query, list_documents)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pinrag.mcp.tools import add_file, add_files, list_documents, query, remove_document
from pinrag.mcp import server as mcp_server


# --- list_documents ---


def test_list_documents_missing_persist_dir_returns_empty() -> None:
    """list_documents returns empty when persist dir does not exist."""
    result = list_documents(persist_dir="/nonexistent/path/xyz", collection="test_coll")
    assert result["documents"] == []
    assert result["total_chunks"] == 0
    assert result["collection_name"] == "test_coll"
    assert "persist_directory" in result


def test_list_documents_returns_documents_from_store(tmp_path: Path) -> None:
    """list_documents returns unique document IDs and total_chunks from Chroma."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    mock_store = MagicMock()
    mock_store.get.return_value = {
        "metadatas": [
            {"file_name": "a.pdf", "page": 1},
            {"file_name": "a.pdf", "page": 2},
            {"document_id": "b.pdf", "page": 1},
        ]
    }

    with patch("pinrag.mcp.tools.get_chroma_store", return_value=mock_store):
        result = list_documents(persist_dir=str(tmp_path), collection="test_coll")

    assert result["documents"] == ["a.pdf", "b.pdf"]
    assert result["total_chunks"] == 3
    assert result["collection_name"] == "test_coll"
    assert "document_details" in result
    mock_store.get.assert_called_once_with(include=["metadatas"])


def test_list_documents_handles_empty_metadatas(tmp_path: Path) -> None:
    """list_documents returns empty list when store has no chunks."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    mock_store = MagicMock()
    mock_store.get.return_value = {"metadatas": []}

    with patch("pinrag.mcp.tools.get_chroma_store", return_value=mock_store):
        result = list_documents(persist_dir=str(tmp_path), collection="test_coll")

    assert result["documents"] == []
    assert result["total_chunks"] == 0
    assert result["document_details"] == {}


def test_list_documents_tag_filter(tmp_path: Path) -> None:
    """list_documents with tag returns only docs with that tag."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    mock_store = MagicMock()
    mock_store.get.return_value = {
        "metadatas": [
            {"document_id": "a.pdf", "tag": "amiga"},
            {"document_id": "a.pdf", "tag": "amiga"},
            {"document_id": "b.pdf", "tag": "pico"},
        ]
    }

    with patch("pinrag.mcp.tools.get_chroma_store", return_value=mock_store):
        result = list_documents(persist_dir=str(tmp_path), collection="c", tag="amiga")

    assert result["documents"] == ["a.pdf"]
    assert result["total_chunks"] == 2
    assert result["document_details"]["a.pdf"]["tag"] == "amiga"


def test_list_documents_includes_document_details_when_present(tmp_path: Path) -> None:
    """list_documents returns document_details when chunks have them."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    mock_store = MagicMock()
    mock_store.get.return_value = {
        "metadatas": [
            {"document_id": "doc.pdf", "upload_timestamp": "2025-01-15T12:00:00Z", "doc_pages": 56, "doc_bytes": 12345, "doc_total_chunks": 224, "tag": "amiga"},
            {"document_id": "doc.pdf", "upload_timestamp": "2025-01-15T12:00:00Z", "doc_pages": 56, "doc_bytes": 12345, "doc_total_chunks": 224, "tag": "amiga"},
        ]
    }

    with patch("pinrag.mcp.tools.get_chroma_store", return_value=mock_store):
        result = list_documents(persist_dir=str(tmp_path), collection="test_coll")

    assert result["documents"] == ["doc.pdf"]
    assert result["document_details"]["doc.pdf"] == {
        "upload_timestamp": "2025-01-15T12:00:00Z",
        "pages": 56,
        "bytes": 12345,
        "chunks": 224,
        "tag": "amiga",
    }


def test_list_documents_aggregates_bytes_across_files(tmp_path: Path) -> None:
    """list_documents sums doc_bytes across unique files (GitHub: many files per doc_id)."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    mock_store = MagicMock()
    mock_store.get.return_value = {
        "metadatas": [
            {"document_id": "owner/repo", "document_type": "github", "file_path": "a.py", "doc_bytes": 100},
            {"document_id": "owner/repo", "document_type": "github", "file_path": "a.py", "doc_bytes": 100},
            {"document_id": "owner/repo", "document_type": "github", "file_path": "b.py", "doc_bytes": 96},
        ]
    }

    with patch("pinrag.mcp.tools.get_chroma_store", return_value=mock_store):
        result = list_documents(persist_dir=str(tmp_path), collection="test_coll")

    assert result["documents"] == ["owner/repo"]
    assert result["document_details"]["owner/repo"]["bytes"] == 196
    assert result["document_details"]["owner/repo"]["file_count"] == 2


def test_list_documents_includes_segments_for_youtube(tmp_path: Path) -> None:
    """list_documents returns segments in document_details for YouTube chunks."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    mock_store = MagicMock()
    mock_store.get.return_value = {
        "metadatas": [
            {"document_id": "dQw4w9WgXcQ", "document_type": "youtube", "upload_timestamp": "2025-01-20T10:00:00Z", "doc_segments": 42, "doc_total_chunks": 15, "doc_title": "Never Gonna Give You Up", "tag": "tutorial"},
            {"document_id": "dQw4w9WgXcQ", "document_type": "youtube", "upload_timestamp": "2025-01-20T10:00:00Z", "doc_segments": 42, "doc_total_chunks": 15, "doc_title": "Never Gonna Give You Up", "tag": "tutorial"},
        ]
    }

    with patch("pinrag.mcp.tools.get_chroma_store", return_value=mock_store):
        result = list_documents(persist_dir=str(tmp_path), collection="test_coll")

    assert result["documents"] == ["dQw4w9WgXcQ"]
    assert result["document_details"]["dQw4w9WgXcQ"]["segments"] == 42
    assert result["document_details"]["dQw4w9WgXcQ"]["chunks"] == 15
    assert result["document_details"]["dQw4w9WgXcQ"]["title"] == "Never Gonna Give You Up"
    assert result["document_details"]["dQw4w9WgXcQ"]["document_type"] == "youtube"


# --- add_file ---


def test_add_file_empty_path_raises() -> None:
    """add_file raises ValueError when path is empty."""
    with pytest.raises(ValueError, match="path cannot be empty"):
        add_file(path="")
    with pytest.raises(ValueError, match="path cannot be empty"):
        add_file(path="   ")


def test_add_file_empty_collection_uses_default(tmp_path: Path) -> None:
    """add_file uses default collection when collection is empty."""
    pdf_file = tmp_path / "dummy.pdf"
    pdf_file.touch()
    with patch("pinrag.mcp.tools.index_pdf") as mock_index:
        mock_index.return_value = MagicMock(
            source_path=pdf_file,
            total_pages=1,
            total_chunks=1,
            persist_directory=tmp_path,
            collection_name="test",
        )
        with patch("pinrag.mcp.tools.get_embedding_model"):
            add_file(path=str(pdf_file), persist_dir=str(tmp_path), collection="")
    mock_index.assert_called_once()


def test_add_file_path_not_found_raises() -> None:
    """add_file raises FileNotFoundError when path does not exist."""
    with pytest.raises(FileNotFoundError, match="Path not found"):
        add_file(path="/nonexistent/file.pdf")


def test_add_file_unsupported_format_raises(tmp_path: Path) -> None:
    """add_file raises ValueError when file format is unsupported."""
    doc_file = tmp_path / "document.docx"
    doc_file.write_bytes(b"PK\x03\x04")  # minimal zip header
    with pytest.raises(ValueError, match="Unsupported format"):
        add_file(path=str(doc_file))


def test_add_file_pdf_success(tmp_path: Path) -> None:
    """add_file returns indexing result when PDF exists and index_pdf succeeds."""
    pdf_file = tmp_path / "sample.pdf"
    pdf_file.touch()
    fake_result = MagicMock()
    fake_result.source_path = pdf_file
    fake_result.total_pages = 5
    fake_result.total_chunks = 12

    with patch("pinrag.mcp.tools.index_pdf", return_value=fake_result) as mock_index:
        with patch("pinrag.mcp.tools.get_embedding_model"):
            result = add_file(
                path=str(pdf_file),
                persist_dir=str(tmp_path),
                collection="test_coll",
            )

    assert result["total_indexed"] == 1
    assert result["indexed"][0]["format"] == "pdf"
    assert result["indexed"][0]["source_path"] == str(pdf_file)
    assert result["indexed"][0]["total_pages"] == 5
    assert result["indexed"][0]["total_chunks"] == 12
    mock_index.assert_called_once()


def test_add_file_plaintext_detection_and_success(tmp_path: Path) -> None:
    """add_file detects plain .txt (no Discord header) and routes to index_plaintext."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Hello world. Plain text content.", encoding="utf-8")
    fake_result = MagicMock()
    fake_result.source_path = txt_file
    fake_result.total_chunks = 2
    fake_result.document_id = "notes.txt"

    with patch("pinrag.mcp.tools.index_plaintext", return_value=fake_result) as mock_index:
        with patch("pinrag.mcp.tools.get_embedding_model"):
            result = add_file(
                path=str(txt_file),
                persist_dir=str(tmp_path),
                collection="test_coll",
            )

    assert result["total_indexed"] == 1
    assert result["indexed"][0]["format"] == "plaintext"
    assert result["indexed"][0]["source_path"] == str(txt_file)
    assert result["indexed"][0]["document_id"] == "notes.txt"
    assert result["indexed"][0]["total_chunks"] == 2
    mock_index.assert_called_once()


def test_add_file_discord_txt_still_detected_as_discord(tmp_path: Path) -> None:
    """add_file treats .txt with Guild:/Channel: as Discord, not plaintext."""
    txt_file = tmp_path / "discord_export.txt"
    txt_file.write_text(
        "Guild: Test Server\nChannel: general\n\n[2024-01-01 12:00] User: Hello",
        encoding="utf-8",
    )
    fake_result = MagicMock()
    fake_result.source_path = txt_file
    fake_result.total_chunks = 5

    with patch("pinrag.mcp.tools.index_discord", return_value=fake_result) as mock_index:
        with patch("pinrag.mcp.tools.get_embedding_model"):
            result = add_file(
                path=str(txt_file),
                persist_dir=str(tmp_path),
                collection="test_coll",
            )

    assert result["total_indexed"] == 1
    assert result["indexed"][0]["format"] == "discord"
    mock_index.assert_called_once()


def test_add_file_with_tag_passes_tag(tmp_path: Path) -> None:
    """add_file passes tag to index_pdf when provided."""
    pdf_file = tmp_path / "sample.pdf"
    pdf_file.touch()
    fake_result = MagicMock()
    fake_result.source_path = pdf_file
    fake_result.total_pages = 5
    fake_result.total_chunks = 12

    with patch("pinrag.mcp.tools.index_pdf", return_value=fake_result) as mock_index:
        with patch("pinrag.mcp.tools.get_embedding_model"):
            add_file(
                path=str(pdf_file),
                persist_dir=str(tmp_path),
                collection="test_coll",
                tag="amiga",
            )

    mock_index.assert_called_once()
    assert mock_index.call_args[1]["tag"] == "amiga"


# --- YouTube ---


def test_add_file_youtube_detection_and_success(tmp_path: Path) -> None:
    """add_file detects YouTube URL and routes to index_youtube."""
    fake_result = MagicMock()
    fake_result.video_id = "dQw4w9WgXcQ"
    fake_result.source_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    fake_result.total_segments = 42
    fake_result.total_chunks = 15

    with patch("pinrag.mcp.tools.index_youtube", return_value=fake_result) as mock_index:
        with patch("pinrag.mcp.tools.get_embedding_model"):
            result = add_file(
                path="https://youtu.be/dQw4w9WgXcQ",
                persist_dir=str(tmp_path),
                collection="test_coll",
            )

    assert result["total_indexed"] == 1
    assert result["indexed"][0]["format"] == "youtube"
    assert result["indexed"][0]["video_id"] == "dQw4w9WgXcQ"
    assert result["indexed"][0]["total_segments"] == 42
    assert result["indexed"][0]["total_chunks"] == 15
    mock_index.assert_called_once_with(
        "https://youtu.be/dQw4w9WgXcQ",
        persist_directory=str(tmp_path),
        collection_name="test_coll",
        embedding=mock_index.call_args[1]["embedding"],
        tag=None,
    )


def test_add_file_local_path_prioritized_over_youtube_id(tmp_path: Path) -> None:
    """add_file treats local file/dir named like YouTube ID as local, not YouTube."""
    pdf_file = tmp_path / "dQw4w9WgXcQ.pdf"
    pdf_file.touch()
    fake_result = MagicMock()
    fake_result.source_path = pdf_file
    fake_result.total_pages = 1
    fake_result.total_chunks = 1

    with patch("pinrag.mcp.tools.index_pdf", return_value=fake_result) as mock_index:
        with patch("pinrag.mcp.tools.get_embedding_model"):
            result = add_file(
                path=str(pdf_file),
                persist_dir=str(tmp_path),
                collection="test_coll",
            )

    assert result["total_indexed"] == 1
    assert result["indexed"][0]["format"] == "pdf"
    mock_index.assert_called_once()


def test_add_file_youtube_transcript_error_returns_failed(tmp_path: Path) -> None:
    """add_file catches transcript errors and returns them in failed."""
    with patch("pinrag.mcp.tools.index_youtube") as mock_index:
        mock_index.side_effect = RuntimeError("No transcript found for YouTube video xyz")
        with patch("pinrag.mcp.tools.get_embedding_model"):
            result = add_file(
                path="https://youtu.be/xyz12345678",
                persist_dir=str(tmp_path),
                collection="test_coll",
            )

    assert result["total_indexed"] == 0
    assert result["total_failed"] == 1
    assert len(result["failed"]) == 1
    assert "No transcript found" in result["failed"][0]["error"]


def test_add_file_youtube_playlist_detection_and_success(tmp_path: Path) -> None:
    """add_file detects playlist URL and routes to index_youtube_playlist."""
    fake_result = MagicMock()
    fake_result.playlist_id = "PLtest"
    fake_result.playlist_title = "Test Playlist"
    fake_result.total_indexed = 2
    fake_result.total_failed = 0
    fake_result.indexed = [
        MagicMock(video_id="abc12345678", source_url="https://www.youtube.com/watch?v=abc12345678", total_segments=2, total_chunks=1, title="V1"),
        MagicMock(video_id="xyz98765432", source_url="https://www.youtube.com/watch?v=xyz98765432", total_segments=3, total_chunks=2, title="V2"),
    ]
    fake_result.failed = []

    with patch("pinrag.mcp.tools.index_youtube_playlist", return_value=fake_result) as mock_index:
        with patch("pinrag.mcp.tools.get_embedding_model"):
            result = add_file(
                path="https://www.youtube.com/playlist?list=PLtest",
                persist_dir=str(tmp_path),
                collection="test_coll",
            )

    assert result["total_indexed"] == 2
    assert len(result["indexed"]) == 2
    assert result["indexed"][0]["format"] == "youtube_playlist"
    assert result["indexed"][0]["video_id"] == "abc12345678"
    assert result["indexed"][1]["video_id"] == "xyz98765432"
    mock_index.assert_called_once_with(
        "https://www.youtube.com/playlist?list=PLtest",
        persist_directory=str(tmp_path),
        collection_name="test_coll",
        embedding=mock_index.call_args[1]["embedding"],
        tag=None,
    )


def test_add_files_tags_length_mismatch_raises() -> None:
    """add_files raises when tags length does not match paths."""
    with pytest.raises(ValueError, match="tags must have same length"):
        add_files(paths=["a.pdf", "b.pdf"], tags=["amiga"])


def test_add_files_empty_paths_raises() -> None:
    """add_files raises ValueError when path list is empty."""
    with pytest.raises(ValueError, match="paths cannot be empty"):
        add_files(paths=[])


def test_add_files_partial_success(tmp_path: Path) -> None:
    """add_files indexes valid files and reports failures per file."""
    good_pdf = tmp_path / "good.pdf"
    bad_ext = tmp_path / "bad.docx"  # unsupported format
    good_pdf.touch()
    bad_ext.write_bytes(b"PK\x03\x04")  # minimal zip header

    fake_result = MagicMock()
    fake_result.source_path = good_pdf
    fake_result.total_pages = 3
    fake_result.total_chunks = 7

    with patch("pinrag.mcp.tools.index_pdf", return_value=fake_result):
        with patch("pinrag.mcp.tools.get_embedding_model"):
            result = add_files(
                paths=[str(good_pdf), str(bad_ext), str(tmp_path / "missing.pdf")],
                persist_dir=str(tmp_path),
                collection="test_coll",
            )

    assert result["total_indexed"] == 1
    assert result["total_failed"] == 2
    assert result["indexed"][0]["source_path"] == str(good_pdf)
    assert len(result["failed"]) == 2
    assert result["fail_summary"] == {"blocked": 0, "disabled": 0, "missing_transcript": 0, "other": 2}


def test_add_files_fail_summary_by_reason() -> None:
    """add_files returns fail_summary categorizing failures: blocked, disabled, missing_transcript, other."""
    from pinrag.mcp.tools import _categorize_failures

    # Unit test for categorization
    failed = [
        {"path": "v1", "error": "YouTube is blocking requests from your IP. Cloud provider."},
        {"path": "v2", "error": "Video xyz has transcripts disabled. Cannot index."},
        {"path": "v3", "error": "Could not retrieve a transcript for the video."},
        {"path": "v4", "error": "No transcript found"},
        {"path": "v5", "error": "File not found"},
    ]
    summary = _categorize_failures(failed)
    assert summary["blocked"] == 1
    assert summary["disabled"] == 1
    assert summary["missing_transcript"] == 2
    assert summary["other"] == 1

    # add_files with failures includes fail_summary
    result = add_files(
        paths=["/nonexistent/a.pdf", "/nonexistent/b.pdf"],
        collection="test_coll",
    )
    assert result["total_failed"] == 2
    assert "fail_summary" in result
    assert result["fail_summary"]["other"] == 2


# --- query ---


def test_query_empty_query_raises() -> None:
    """query raises ValueError when query is empty."""
    with pytest.raises(ValueError, match="Query cannot be empty"):
        query(user_query="")
    with pytest.raises(ValueError, match="Query cannot be empty"):
        query(user_query="   ")


def test_query_uses_config_for_persist_and_collection(tmp_path: Path) -> None:
    """query uses get_persist_dir and get_collection_name from config."""
    from pinrag.rag import RAGResult

    (tmp_path / "chroma_db").mkdir(parents=True, exist_ok=True)
    with patch("pinrag.mcp.tools.get_persist_dir", return_value=str(tmp_path)):
        with patch("pinrag.mcp.tools.get_collection_name", return_value="pinrag"):
            with patch("pinrag.mcp.tools.get_embedding_model"):
                with patch("pinrag.mcp.tools.get_chat_model"):
                    with patch("pinrag.mcp.tools.run_rag") as mock_run:
                        mock_run.return_value = RAGResult(answer="ok", sources=[])
                        query(user_query="test")
    mock_run.assert_called_once()


def test_query_missing_persist_dir_raises() -> None:
    """query raises FileNotFoundError when persist dir does not exist."""
    with patch("pinrag.mcp.tools.get_persist_dir", return_value="/nonexistent/chroma_db"):
        with pytest.raises(FileNotFoundError, match="Persistence directory does not exist"):
            query(user_query="test")


def test_query_chain_error_propagates(tmp_path: Path) -> None:
    """query propagates retrieval/LLM errors from run_rag."""
    (tmp_path / "chroma_db").mkdir(parents=True, exist_ok=True)

    with patch("pinrag.mcp.tools.get_persist_dir", return_value=str(tmp_path)):
        with patch("pinrag.mcp.tools.get_embedding_model"):
            with patch("pinrag.mcp.tools.get_chat_model"):
                with patch(
                    "pinrag.mcp.tools.run_rag",
                    side_effect=RuntimeError("OpenAI API rate limit"),
                ):
                    with pytest.raises(RuntimeError, match="OpenAI API rate limit"):
                        query(user_query="test")


def test_query_success(tmp_path: Path) -> None:
    """query returns answer and sources when run_rag succeeds."""
    from pinrag.rag import RAGResult

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

    with patch("pinrag.mcp.tools.get_persist_dir", return_value=str(tmp_path)):
        with patch("pinrag.mcp.tools.get_collection_name", return_value="test_coll"):
            with patch("pinrag.mcp.tools.get_embedding_model"):
                with patch("pinrag.mcp.tools.get_chat_model"):
                    with patch("pinrag.mcp.tools.run_rag", mock_run_rag):
                        result = query(user_query="What is the answer?")

    assert result["answer"] == "The answer is 42."
    assert len(result["sources"]) == 2
    assert result["sources"][0] == {"document_id": "doc.pdf", "page": 1}
    assert result["sources"][1] == {"document_id": "doc.pdf", "page": 2}
    mock_run_rag.assert_called_once()


def test_query_sources_include_start_for_youtube(tmp_path: Path) -> None:
    """query returns start (timestamp) in sources when present (YouTube)."""
    from pinrag.rag import RAGResult

    (tmp_path / "chroma_db").mkdir(parents=True, exist_ok=True)
    mock_run_rag = MagicMock(
        return_value=RAGResult(
            answer="From the video.",
            sources=[
                {"document_id": "dQw4w9WgXcQ", "page": 0, "start": 83},
                {"document_id": "dQw4w9WgXcQ", "page": 0, "start": 120},
            ],
        )
    )

    with patch("pinrag.mcp.tools.get_persist_dir", return_value=str(tmp_path)):
        with patch("pinrag.mcp.tools.get_collection_name", return_value="test_coll"):
            with patch("pinrag.mcp.tools.get_embedding_model"):
                with patch("pinrag.mcp.tools.get_chat_model"):
                    with patch("pinrag.mcp.tools.run_rag", mock_run_rag):
                        result = query(user_query="What does the video say?")

    assert result["sources"][0] == {"document_id": "dQw4w9WgXcQ", "page": 0, "start": 83}
    assert result["sources"][1] == {"document_id": "dQw4w9WgXcQ", "page": 0, "start": 120}
    assert mock_run_rag.call_args[0][0] == "What does the video say?"


def test_query_page_range_validation() -> None:
    """query raises when page_min or page_max is provided without the other."""
    with pytest.raises(ValueError, match="page_min and page_max must be provided together"):
        query(user_query="test", page_min=1)
    with pytest.raises(ValueError, match="page_min and page_max must be provided together"):
        query(user_query="test", page_max=10)
    with pytest.raises(ValueError, match="page_min must be <= page_max"):
        query(user_query="test", page_min=10, page_max=1)


def test_query_with_page_range(tmp_path: Path) -> None:
    """query passes page_min and page_max to run_rag when provided."""
    from pinrag.rag import RAGResult

    (tmp_path / "chroma_db").mkdir(parents=True, exist_ok=True)
    mock_run_rag = MagicMock(
        return_value=RAGResult(
            answer="Page 16 content.",
            sources=[{"document_id": "pico.pdf", "page": 16}],
        )
    )

    with patch("pinrag.mcp.tools.get_persist_dir", return_value=str(tmp_path)):
        with patch("pinrag.mcp.tools.get_collection_name", return_value="test_coll"):
            with patch("pinrag.mcp.tools.get_embedding_model"):
                with patch("pinrag.mcp.tools.get_chat_model"):
                    with patch("pinrag.mcp.tools.run_rag", mock_run_rag):
                        query(
                            user_query="OpenOCD?",
                            document_id="pico.pdf",
                            page_min=16,
                            page_max=16,
                        )

    mock_run_rag.assert_called_once()
    assert mock_run_rag.call_args[1]["page_min"] == 16
    assert mock_run_rag.call_args[1]["page_max"] == 16


def test_query_with_document_type_filter(tmp_path: Path) -> None:
    """query passes document_type to run_rag when provided."""
    from pinrag.rag import RAGResult

    (tmp_path / "chroma_db").mkdir(parents=True, exist_ok=True)
    mock_run_rag = MagicMock(
        return_value=RAGResult(
            answer="From YouTube.",
            sources=[{"document_id": "bwgLXEQdq20", "page": 0, "start": 664}],
        )
    )

    with patch("pinrag.mcp.tools.get_persist_dir", return_value=str(tmp_path)):
        with patch("pinrag.mcp.tools.get_collection_name", return_value="test_coll"):
            with patch("pinrag.mcp.tools.get_embedding_model"):
                with patch("pinrag.mcp.tools.get_chat_model"):
                    with patch("pinrag.mcp.tools.run_rag", mock_run_rag):
                        query(user_query="OTG?", document_type="youtube")

    mock_run_rag.assert_called_once()
    assert mock_run_rag.call_args[1]["document_type"] == "youtube"


def test_query_with_tag_filter(tmp_path: Path) -> None:
    """query passes tag to run_rag when provided."""
    from pinrag.rag import RAGResult

    (tmp_path / "chroma_db").mkdir(parents=True, exist_ok=True)
    mock_run_rag = MagicMock(
        return_value=RAGResult(
            answer="From PI_PICO docs.",
            sources=[{"document_id": "pico.pdf", "page": 1}],
        )
    )

    with patch("pinrag.mcp.tools.get_persist_dir", return_value=str(tmp_path)):
        with patch("pinrag.mcp.tools.get_collection_name", return_value="test_coll"):
            with patch("pinrag.mcp.tools.get_embedding_model"):
                with patch("pinrag.mcp.tools.get_chat_model"):
                    with patch("pinrag.mcp.tools.run_rag", mock_run_rag):
                        query(user_query="GPIO?", tag="PI_PICO")

    mock_run_rag.assert_called_once()
    assert mock_run_rag.call_args[1]["tag"] == "PI_PICO"


def test_query_with_document_id_filter(tmp_path: Path) -> None:
    """query passes document_id to run_rag when provided."""
    from pinrag.rag import RAGResult

    (tmp_path / "chroma_db").mkdir(parents=True, exist_ok=True)
    mock_run_rag = MagicMock(
        return_value=RAGResult(
            answer="Filtered answer.",
            sources=[{"document_id": "pico.pdf", "page": 1}],
        )
    )

    with patch("pinrag.mcp.tools.get_persist_dir", return_value=str(tmp_path)):
        with patch("pinrag.mcp.tools.get_collection_name", return_value="test_coll"):
            with patch("pinrag.mcp.tools.get_embedding_model"):
                with patch("pinrag.mcp.tools.get_chat_model"):
                    with patch("pinrag.mcp.tools.run_rag", mock_run_rag):
                        query(
                            user_query="GPIO?",
                            document_id="RP-008276-DS-1-getting-started-with-pico.pdf",
                        )

    mock_run_rag.assert_called_once()
    assert mock_run_rag.call_args[1]["document_id"] == "RP-008276-DS-1-getting-started-with-pico.pdf"


# --- server_config_resource ---


def test_server_config_resource_includes_api_key_status() -> None:
    """server_config_resource shows API key set/not set, never the values."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-secret"}, clear=False):
        out = asyncio.run(mcp_server.server_config_resource())
    assert "OPENAI_API_KEY: set" in out
    assert "sk-secret" not in out
    assert "ANTHROPIC_API_KEY:" in out
    assert "COHERE_API_KEY:" in out


def test_server_config_resource_includes_effective_config() -> None:
    """server_config_resource includes effective config from get_* functions."""
    with patch("pinrag.mcp.server.get_persist_dir", return_value="/my/chroma"):
        with patch("pinrag.mcp.server.get_collection_name", return_value="my_coll"):
            out = asyncio.run(mcp_server.server_config_resource())
    assert "PINRAG_PERSIST_DIR: /my/chroma" in out
    assert "PINRAG_COLLECTION_NAME: my_coll" in out
    assert "PINRAG_LOG_TO_STDERR:" in out
    assert "PINRAG_LOG_LEVEL:" in out
    assert "--- Set (from env) ---" in out
    assert "--- Defaults (not set) ---" in out
    assert "--- API keys (sensitive; only status) ---" in out


def test_server_config_resource_shows_set_vs_default() -> None:
    """server_config_resource marks set vars vs (default) for unset."""
    with patch.dict(
        "os.environ",
        {"PINRAG_PERSIST_DIR": "/custom/db"},
        clear=False,
    ):
        out = asyncio.run(mcp_server.server_config_resource())
    assert "PINRAG_PERSIST_DIR: /custom/db" in out
    assert " (default)" in out  # at least one unset var shows (default)


def test_server_config_resource_unset_var_shows_default() -> None:
    """server_config_resource shows (default) for vars not in env."""
    env_no_pinrag = {k: v for k, v in __import__("os").environ.items() if not k.startswith("PINRAG_")}
    with patch.dict("os.environ", env_no_pinrag, clear=True):
        out = asyncio.run(mcp_server.server_config_resource())
    assert "(default)" in out


# --- remove_document ---


def test_remove_document_deletes_parent_chunks_when_parent_child_enabled(tmp_path: Path) -> None:
    """remove_document deletes both Chroma children and docstore parents when parent-child is on."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    mock_store = MagicMock()
    # First call: get chunks by document_id; second: check if parent is referenced elsewhere
    mock_store.get.side_effect = [
        {
            "ids": ["child1", "child2"],
            "metadatas": [
                {"doc_id": "parent-uuid-1", "document_id": "doc.pdf"},
                {"doc_id": "parent-uuid-1", "document_id": "doc.pdf"},
            ],
        },
        {"metadatas": [{"document_id": "doc.pdf"}]},  # parent only ref'd by doc.pdf
    ]
    mock_docstore = MagicMock()

    with patch("pinrag.mcp.tools.get_chroma_store", return_value=mock_store):
        with patch("pinrag.mcp.tools.get_use_parent_child", return_value=True):
            with patch("pinrag.mcp.tools.get_parent_docstore", return_value=mock_docstore):
                result = remove_document(
                    document_id="doc.pdf",
                    persist_dir=str(tmp_path),
                    collection="test_coll",
                )

    assert result["deleted_chunks"] == 2
    assert result["document_id"] == "doc.pdf"
    mock_docstore.mdelete.assert_called_once()
    assert set(mock_docstore.mdelete.call_args[0][0]) == {"parent-uuid-1"}
    mock_store.delete.assert_called_once_with(where={"document_id": "doc.pdf"})


def test_remove_document_skips_docstore_when_parent_child_disabled(tmp_path: Path) -> None:
    """remove_document does not touch docstore when parent-child is off."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    mock_store = MagicMock()
    mock_store.get.return_value = {"ids": ["c1"], "metadatas": [{}]}

    with patch("pinrag.mcp.tools.get_chroma_store", return_value=mock_store):
        with patch("pinrag.mcp.tools.get_use_parent_child", return_value=False):
            with patch("pinrag.mcp.tools.get_parent_docstore") as mock_get_docstore:
                remove_document(document_id="doc.pdf", persist_dir=str(tmp_path), collection="c")
    mock_get_docstore.assert_not_called()


# --- Error handling: propagate + log ---


def test_server_tool_logs_on_failure() -> None:
    """When a tool raises, the server decorator logs the exception then re-raises."""
    mock_log = MagicMock()
    with patch.object(mcp_server, "_log", mock_log):
        with pytest.raises(ValueError, match="Query cannot be empty"):
            asyncio.run(mcp_server.query_tool(query=""))
    mock_log.exception.assert_called_once()
