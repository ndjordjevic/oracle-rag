"""Unit tests for YouTube transcript loader, indexer, and citation formatting."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from oracle_rag.indexing.youtube_loader import (
    _fetch_video_title,
    extract_video_id,
    load_youtube_transcript_as_documents,
)
from oracle_rag.rag.formatting import format_docs, format_sources
from langchain_core.documents import Document


# --- extract_video_id ---


def test_extract_video_id_bare_id() -> None:
    """extract_video_id returns bare 11-char video ID."""
    assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("abc123XYZ-_") == "abc123XYZ-_"


def test_extract_video_id_youtube_watch() -> None:
    """extract_video_id extracts from youtube.com/watch?v=ID."""
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("https://youtube.com/watch?v=xyz12345678") == "xyz12345678"


def test_extract_video_id_youtu_be() -> None:
    """extract_video_id extracts from youtu.be/ID."""
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_embed() -> None:
    """extract_video_id extracts from youtube.com/embed/ID."""
    assert extract_video_id("https://www.youtube.com/embed/abc12345678") == "abc12345678"


def test_extract_video_id_invalid_returns_none() -> None:
    """extract_video_id returns None for invalid input."""
    assert extract_video_id("") is None
    assert extract_video_id("   ") is None
    assert extract_video_id("https://example.com/foo") is None
    assert extract_video_id("short") is None
    assert extract_video_id("toolong12345") is None


# --- _fetch_video_title ---


def test_fetch_video_title_success() -> None:
    """_fetch_video_title returns title from oEmbed when available."""

    class FakeResponse:
        def read(self):
            return b'{"title": "Rick Astley - Never Gonna Give You Up"}'

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

    with patch("oracle_rag.indexing.youtube_loader.urllib.request.urlopen", return_value=FakeResponse()):
        title = _fetch_video_title("dQw4w9WgXcQ")
    assert title == "Rick Astley - Never Gonna Give You Up"


def test_fetch_video_title_returns_none_on_error() -> None:
    """_fetch_video_title returns None when fetch fails."""
    with patch("oracle_rag.indexing.youtube_loader.urllib.request.urlopen", side_effect=Exception("network error")):
        title = _fetch_video_title("dQw4w9WgXcQ")
    assert title is None


# --- load_youtube_transcript_as_documents ---


def test_load_youtube_transcript_invalid_url_raises() -> None:
    """load_youtube_transcript_as_documents raises ValueError for invalid URL."""
    with pytest.raises(ValueError, match="Invalid YouTube URL or video ID"):
        load_youtube_transcript_as_documents("not-a-youtube-url")


def test_load_youtube_transcript_success() -> None:
    """load_youtube_transcript_as_documents returns Documents with metadata."""
    mock_segment = MagicMock()
    mock_segment.text = "Hello world"
    mock_segment.start = 0.0
    mock_segment.duration = 2.5

    with patch("youtube_transcript_api.YouTubeTranscriptApi") as mock_api:
        mock_instance = MagicMock()
        mock_instance.fetch.return_value = [mock_segment]
        mock_api.return_value = mock_instance
        with patch("oracle_rag.indexing.youtube_loader._fetch_video_title", return_value="Test Video Title"):
            result = load_youtube_transcript_as_documents("https://youtu.be/dQw4w9WgXcQ")

    assert result.video_id == "dQw4w9WgXcQ"
    assert result.source_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert result.title == "Test Video Title"
    assert result.total_segments == 1
    assert len(result.documents) == 1
    doc = result.documents[0]
    assert doc.page_content == "Hello world"
    assert doc.metadata["document_id"] == "dQw4w9WgXcQ"
    assert doc.metadata["document_type"] == "youtube"
    assert doc.metadata["video_id"] == "dQw4w9WgXcQ"
    assert doc.metadata["title"] == "Test Video Title"
    assert doc.metadata["start"] == 0
    assert doc.metadata["duration"] == 2.5
    assert "youtube.com" in doc.metadata["source"]


def test_load_youtube_transcript_transcripts_disabled_raises() -> None:
    """load_youtube_transcript_as_documents raises RuntimeError when transcripts disabled."""
    from youtube_transcript_api import TranscriptsDisabled

    with patch("youtube_transcript_api.YouTubeTranscriptApi") as mock_api:
        mock_instance = MagicMock()
        mock_instance.fetch.side_effect = TranscriptsDisabled("xyz")
        mock_instance.list.side_effect = TranscriptsDisabled("xyz")
        mock_api.return_value = mock_instance

        with pytest.raises(RuntimeError, match="transcripts disabled"):
            load_youtube_transcript_as_documents("https://youtu.be/xyz12345678")


def test_load_youtube_transcript_no_transcript_raises() -> None:
    """load_youtube_transcript_as_documents raises RuntimeError when no transcript found."""
    from youtube_transcript_api import NoTranscriptFound

    with patch("youtube_transcript_api.YouTubeTranscriptApi") as mock_api:
        mock_instance = MagicMock()
        mock_instance.fetch.side_effect = NoTranscriptFound("xyz", None, None)
        mock_instance.list.side_effect = NoTranscriptFound("xyz", None, None)
        mock_api.return_value = mock_instance

        with pytest.raises(RuntimeError, match="No transcript found"):
            load_youtube_transcript_as_documents("https://youtu.be/xyz12345678")


def test_load_youtube_transcript_none_without_error_raises() -> None:
    """load_youtube_transcript_as_documents raises RuntimeError when transcript is None and last_error is None."""
    mock_fetch_none = MagicMock()
    mock_fetch_none.fetch.return_value = None
    mock_transcript_item = MagicMock()
    mock_transcript_item.fetch.return_value = None

    transcript_list = MagicMock()
    transcript_list._manually_created_transcripts = {}
    transcript_list._generated_transcripts = {}
    transcript_list.find_manually_created_transcript.return_value = mock_fetch_none
    transcript_list.find_generated_transcript.return_value = mock_fetch_none
    transcript_list.__iter__ = lambda self: iter([mock_transcript_item])

    with patch("youtube_transcript_api.YouTubeTranscriptApi") as mock_api:
        mock_instance = MagicMock()
        mock_instance.list.return_value = transcript_list
        mock_api.return_value = mock_instance

        with pytest.raises(RuntimeError, match="No transcript available and no error was captured"):
            load_youtube_transcript_as_documents("https://youtu.be/xyz12345678", languages=())


# --- format_sources (timestamp citations) ---


def test_format_sources_includes_start_for_youtube() -> None:
    """format_sources returns start when present (YouTube chunks)."""
    docs = [
        Document(page_content="Hello", metadata={"document_id": "vid1", "start": 83, "page": 1}),
        Document(page_content="World", metadata={"document_id": "vid1", "start": 120}),
    ]
    sources = format_sources(docs)
    assert len(sources) == 2
    assert sources[0] == {"document_id": "vid1", "page": 0, "start": 83}
    assert sources[1] == {"document_id": "vid1", "page": 0, "start": 120}


def test_format_sources_page_for_pdf() -> None:
    """format_sources returns page for PDF chunks (no start)."""
    docs = [
        Document(page_content="Page 1", metadata={"document_id": "doc.pdf", "page": 1}),
        Document(page_content="Page 2", metadata={"document_id": "doc.pdf", "page": 2}),
    ]
    sources = format_sources(docs)
    assert sources[0] == {"document_id": "doc.pdf", "page": 1}
    assert sources[1] == {"document_id": "doc.pdf", "page": 2}


def test_format_docs_citation_label_timestamp() -> None:
    """format_docs uses t. M:SS for chunks with start (YouTube)."""
    docs = [
        Document(page_content="Hello", metadata={"document_id": "vid1", "start": 83}),
    ]
    out = format_docs(docs, number_chunks=True)
    assert "t. 1:23" in out
    assert "doc: vid1" in out


def test_format_docs_citation_label_page() -> None:
    """format_docs uses p. N for chunks with page (PDF)."""
    docs = [
        Document(page_content="Page 16", metadata={"document_id": "doc.pdf", "page": 16}),
    ]
    out = format_docs(docs, number_chunks=True)
    assert "p. 16" in out
    assert "doc: doc.pdf" in out
