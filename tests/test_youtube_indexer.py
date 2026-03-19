"""Unit tests for YouTube indexer (index_youtube)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from pinrag.indexing.youtube_indexer import (
    YouTubeIndexResult,
    YouTubePlaylistIndexResult,
    index_youtube,
    index_youtube_playlist,
)
from pinrag.indexing.youtube_loader import YouTubeLoadResult


class _MockEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 1536 for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.1] * 1536


def _make_load_result(
    video_id: str = "dQw4w9WgXcQ",
    title: str = "Test Video",
    num_segments: int = 3,
) -> YouTubeLoadResult:
    docs = []
    for i in range(num_segments):
        docs.append(
            Document(
                page_content=f"Segment {i} text content here",
                metadata={
                    "document_id": video_id,
                    "document_type": "youtube",
                    "video_id": video_id,
                    "title": title,
                    "start": i * 30,
                    "duration": 25.0,
                    "source": f"https://www.youtube.com/watch?v={video_id}",
                },
            )
        )
    return YouTubeLoadResult(
        video_id=video_id,
        source_url=f"https://www.youtube.com/watch?v={video_id}",
        title=title,
        documents=docs,
        total_segments=num_segments,
    )


@patch("pinrag.indexing.youtube_indexer.get_use_parent_child", return_value=False)
@patch("pinrag.indexing.youtube_indexer.load_youtube_transcript_as_documents")
def test_index_youtube_smoke(
    mock_load: MagicMock, mock_pc: MagicMock, tmp_path: Path
) -> None:
    """Index mocked transcript; verify result and Chroma contents."""
    mock_load.return_value = _make_load_result()
    persist = str(tmp_path / "chroma")

    result = index_youtube(
        "https://youtu.be/dQw4w9WgXcQ",
        persist_directory=persist,
        collection_name="test_yt",
        embedding=_MockEmbeddings(),
    )

    assert isinstance(result, YouTubeIndexResult)
    assert result.video_id == "dQw4w9WgXcQ"
    assert result.title == "Test Video"
    assert result.total_segments == 3
    assert result.total_chunks > 0

    from pinrag.vectorstore import get_chroma_store

    store = get_chroma_store(
        persist_directory=persist,
        collection_name="test_yt",
        embedding=_MockEmbeddings(),
    )
    docs = store.similarity_search("Segment", k=5)
    assert len(docs) > 0
    assert docs[0].metadata.get("document_type") == "youtube"


@patch("pinrag.indexing.youtube_indexer.get_use_parent_child", return_value=False)
@patch("pinrag.indexing.youtube_indexer.load_youtube_transcript_as_documents")
def test_index_youtube_replaces_on_reindex(
    mock_load: MagicMock, mock_pc: MagicMock, tmp_path: Path
) -> None:
    """Indexing same video twice replaces chunks (no duplicates)."""
    mock_load.return_value = _make_load_result()
    persist = str(tmp_path / "chroma")
    emb = _MockEmbeddings()

    r1 = index_youtube(
        "dQw4w9WgXcQ",
        persist_directory=persist,
        collection_name="test_coll",
        embedding=emb,
    )
    r2 = index_youtube(
        "dQw4w9WgXcQ",
        persist_directory=persist,
        collection_name="test_coll",
        embedding=emb,
    )

    assert r2.total_chunks == r1.total_chunks


@patch("pinrag.indexing.youtube_indexer.get_use_parent_child", return_value=False)
@patch("pinrag.indexing.youtube_indexer.load_youtube_transcript_as_documents")
def test_index_youtube_empty_transcript(
    mock_load: MagicMock, mock_pc: MagicMock, tmp_path: Path
) -> None:
    """Empty transcript results in 0 chunks and deletes old data."""
    empty_result = YouTubeLoadResult(
        video_id="xyz12345678",
        source_url="https://www.youtube.com/watch?v=xyz12345678",
        title="Empty",
        documents=[],
        total_segments=0,
    )
    mock_load.return_value = empty_result
    persist = str(tmp_path / "chroma")

    result = index_youtube(
        "xyz12345678",
        persist_directory=persist,
        collection_name="test_empty",
        embedding=_MockEmbeddings(),
    )

    assert result.total_segments == 0
    assert result.total_chunks == 0


@patch("pinrag.indexing.youtube_indexer.get_use_parent_child", return_value=False)
@patch("pinrag.indexing.youtube_indexer.load_youtube_transcript_as_documents")
def test_index_youtube_with_tag(
    mock_load: MagicMock, mock_pc: MagicMock, tmp_path: Path
) -> None:
    """Tag is propagated to chunk metadata."""
    mock_load.return_value = _make_load_result()
    persist = str(tmp_path / "chroma")

    index_youtube(
        "dQw4w9WgXcQ",
        persist_directory=persist,
        collection_name="test_tag",
        embedding=_MockEmbeddings(),
        tag="LECTURES",
    )

    from pinrag.vectorstore import get_chroma_store

    store = get_chroma_store(
        persist_directory=persist,
        collection_name="test_tag",
        embedding=_MockEmbeddings(),
    )
    docs = store.similarity_search("Segment", k=5)
    assert all(d.metadata.get("tag") == "LECTURES" for d in docs)


@patch("pinrag.indexing.youtube_indexer.get_use_parent_child", return_value=False)
@patch("pinrag.indexing.youtube_indexer.load_youtube_transcript_as_documents")
def test_index_youtube_metadata_fields(
    mock_load: MagicMock, mock_pc: MagicMock, tmp_path: Path
) -> None:
    """Indexed chunks have expected metadata fields."""
    mock_load.return_value = _make_load_result()
    persist = str(tmp_path / "chroma")

    index_youtube(
        "dQw4w9WgXcQ",
        persist_directory=persist,
        collection_name="test_meta",
        embedding=_MockEmbeddings(),
    )

    from pinrag.vectorstore import get_chroma_store

    store = get_chroma_store(
        persist_directory=persist,
        collection_name="test_meta",
        embedding=_MockEmbeddings(),
    )
    docs = store.similarity_search("Segment", k=1)
    meta = docs[0].metadata
    assert meta["document_type"] == "youtube"
    assert "upload_timestamp" in meta
    assert "doc_total_chunks" in meta
    assert "doc_bytes" in meta


# --- index_youtube_playlist ---


@patch("pinrag.indexing.youtube_indexer.index_youtube")
@patch("pinrag.indexing.youtube_indexer.fetch_playlist_info")
def test_index_youtube_playlist_smoke(
    mock_fetch: MagicMock,
    mock_index: MagicMock,
    tmp_path: Path,
) -> None:
    """index_youtube_playlist fetches video IDs and indexes each via index_youtube."""
    mock_fetch.return_value = {
        "playlist_id": "PLtest",
        "playlist_title": "Test Playlist",
        "video_ids": ["abc12345678", "xyz98765432"],
    }
    mock_index.side_effect = [
        YouTubeIndexResult(
            video_id="abc12345678",
            source_url="https://www.youtube.com/watch?v=abc12345678",
            total_segments=2,
            total_chunks=1,
            persist_directory=tmp_path / "chroma",
            collection_name="test",
            title="Video 1",
        ),
        YouTubeIndexResult(
            video_id="xyz98765432",
            source_url="https://www.youtube.com/watch?v=xyz98765432",
            total_segments=3,
            total_chunks=2,
            persist_directory=tmp_path / "chroma",
            collection_name="test",
            title="Video 2",
        ),
    ]

    result = index_youtube_playlist(
        "https://www.youtube.com/playlist?list=PLtest",
        persist_directory=str(tmp_path / "chroma"),
        collection_name="test",
        embedding=_MockEmbeddings(),
    )

    assert isinstance(result, YouTubePlaylistIndexResult)
    assert result.playlist_id == "PLtest"
    assert result.playlist_title == "Test Playlist"
    assert result.total_indexed == 2
    assert result.total_failed == 0
    assert len(result.indexed) == 2
    assert result.indexed[0].video_id == "abc12345678"
    assert result.indexed[1].video_id == "xyz98765432"
    assert mock_index.call_count == 2
    calls = mock_index.call_args_list
    assert calls[0][0][0] == "abc12345678"
    assert calls[1][0][0] == "xyz98765432"
    assert calls[0][1]["extra_metadata"] == {
        "playlist_id": "PLtest",
        "playlist_title": "Test Playlist",
    }


@patch("pinrag.indexing.youtube_indexer.index_youtube")
@patch("pinrag.indexing.youtube_indexer.fetch_playlist_info")
def test_index_youtube_playlist_partial_failure(
    mock_fetch: MagicMock,
    mock_index: MagicMock,
    tmp_path: Path,
) -> None:
    """index_youtube_playlist continues on per-video failure and reports failed."""
    mock_fetch.return_value = {
        "playlist_id": "PLx",
        "playlist_title": "",
        "video_ids": ["ok123456789", "fail1234567"],
    }
    mock_index.side_effect = [
        YouTubeIndexResult(
            video_id="ok123456789",
            source_url="https://www.youtube.com/watch?v=ok123456789",
            total_segments=1,
            total_chunks=1,
            persist_directory=tmp_path / "chroma",
            collection_name="test",
            title=None,
        ),
        RuntimeError("No transcript found"),
    ]

    result = index_youtube_playlist(
        "https://www.youtube.com/playlist?list=PLx",
        persist_directory=str(tmp_path / "chroma"),
        collection_name="test",
        embedding=_MockEmbeddings(),
    )

    assert result.total_indexed == 1
    assert result.total_failed == 1
    assert len(result.failed) == 1
    assert result.failed[0]["video_id"] == "fail1234567"
    assert "No transcript found" in result.failed[0]["error"]


def test_index_youtube_playlist_invalid_url_raises() -> None:
    """index_youtube_playlist raises ValueError for non-playlist URL."""
    with pytest.raises(ValueError, match="Invalid YouTube playlist URL"):
        index_youtube_playlist("https://youtu.be/dQw4w9WgXcQ")
