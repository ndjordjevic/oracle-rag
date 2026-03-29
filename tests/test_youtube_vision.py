"""Tests for optional YouTube vision enrichment."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from pinrag.indexing.youtube_loader import YouTubeLoadResult
from pinrag.indexing.youtube_vision import (
    ExtractedFrame,
    FrameAnalysis,
    enrich_with_vision,
    merge_transcript_and_frames,
)


def _make_transcript_docs(video_id: str = "abc12345678") -> list[Document]:
    return [
        Document(
            page_content="Intro to the project.",
            metadata={
                "document_id": video_id,
                "document_type": "youtube",
                "video_id": video_id,
                "start": 0,
                "duration": 9.0,
                "source": f"https://www.youtube.com/watch?v={video_id}",
            },
        ),
        Document(
            page_content="Now writing code in main.c.",
            metadata={
                "document_id": video_id,
                "document_type": "youtube",
                "video_id": video_id,
                "start": 10,
                "duration": 12.0,
                "source": f"https://www.youtube.com/watch?v={video_id}",
            },
        ),
    ]


def test_merge_transcript_and_frames_aligns_by_timestamp() -> None:
    """Frame descriptions are merged into the closest/containing transcript segment."""
    docs = _make_transcript_docs()
    analyses = [
        FrameAnalysis(timestamp=2.0, description="Terminal shows ls -la.", scene_index=0),
        FrameAnalysis(
            timestamp=15.0,
            description="Editor with C code: int main(void) { ... }",
            scene_index=1,
        ),
        FrameAnalysis(
            timestamp=16.0, description="Compiler output: build succeeded.", scene_index=2
        ),
    ]

    merged = merge_transcript_and_frames(docs, analyses)

    assert len(merged) == 2
    assert merged[0].page_content.startswith("[Narrator] Intro to the project.")
    assert "[On-screen at 2s] Terminal shows ls -la." in merged[0].page_content

    assert merged[1].page_content.startswith("[Narrator] Now writing code in main.c.")
    assert "int main(void)" in merged[1].page_content
    assert "build succeeded" in merged[1].page_content
    assert merged[1].metadata["has_visual"] is True
    assert merged[1].metadata["frame_count"] == 2
    assert merged[1].metadata["visual_source"] == "scene_detect"


@patch("pinrag.indexing.youtube_vision.analyze_frames")
@patch("pinrag.indexing.youtube_vision.extract_frames")
@patch("pinrag.indexing.youtube_vision.download_video")
def test_enrich_with_vision_merges_into_load_result(
    mock_download: MagicMock, mock_extract: MagicMock, mock_analyze: MagicMock, tmp_path: Path
) -> None:
    """enrich_with_vision returns a new YouTubeLoadResult with merged visual text."""
    docs = _make_transcript_docs("xyz98765432")
    load_result = YouTubeLoadResult(
        video_id="xyz98765432",
        source_url="https://www.youtube.com/watch?v=xyz98765432",
        documents=docs,
        total_segments=2,
        title="Sample",
    )
    mock_download.return_value = tmp_path / "video.mp4"
    mock_extract.return_value = [
        ExtractedFrame(timestamp=12.0, image_path=tmp_path / "f0.png", scene_index=0)
    ]
    mock_analyze.return_value = [
        FrameAnalysis(
            timestamp=12.0,
            description="Code editor shows function setup() and loop().",
            scene_index=0,
        )
    ]

    with patch.dict(
        os.environ,
        {
            "PINRAG_VISION_PROVIDER": "openai",
            "PINRAG_VISION_MODEL": "gpt-4o-mini",
            "PINRAG_YT_VISION_MAX_FRAMES": "5",
            "PINRAG_YT_VISION_MIN_SCENE_SCORE": "20",
        },
        clear=False,
    ):
        enriched = enrich_with_vision(load_result)

    assert enriched.video_id == load_result.video_id
    assert enriched.total_segments == load_result.total_segments
    assert "setup() and loop()" in enriched.documents[1].page_content
    assert enriched.documents[1].metadata["has_visual"] is True


@pytest.mark.integration
def test_enrich_with_vision_full_pipeline_live() -> None:
    """Exercise full vision flow with deterministic mocks (no network-only skip)."""
    docs = _make_transcript_docs("9u82Uy_458E")
    load_result = YouTubeLoadResult(
        video_id="9u82Uy_458E",
        source_url="https://www.youtube.com/watch?v=9u82Uy_458E",
        documents=docs,
        total_segments=2,
        title="Vision Pipeline",
    )

    with (
        patch("pinrag.indexing.youtube_vision.download_video") as mock_download,
        patch("pinrag.indexing.youtube_vision.extract_frames") as mock_extract,
        patch("pinrag.indexing.youtube_vision.analyze_frames") as mock_analyze,
    ):
        mock_download.return_value = Path("/tmp/video.mp4")
        mock_extract.return_value = [
            ExtractedFrame(
                timestamp=11.0,
                image_path=Path("/tmp/f0.png"),
                scene_index=0,
            )
        ]
        mock_analyze.return_value = [
            FrameAnalysis(
                timestamp=11.0,
                description="Live-like pipeline check.",
                scene_index=0,
            )
        ]

        with patch.dict(
            os.environ,
            {
                "PINRAG_VISION_PROVIDER": "openai",
                "PINRAG_VISION_MODEL": "gpt-4o-mini",
                "PINRAG_YT_VISION_MAX_FRAMES": "2",
                "PINRAG_YT_VISION_MIN_SCENE_SCORE": "25",
            },
            clear=False,
        ):
            enriched = enrich_with_vision(load_result)

    assert len(enriched.documents) == len(load_result.documents)
    assert any(d.metadata.get("has_visual") for d in enriched.documents)
