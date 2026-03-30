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
    _fix_llm_json,
    _parse_openrouter_video_segments,
    analyze_frames,
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
            "PINRAG_YT_VISION_PROVIDER": "openai",
            "PINRAG_YT_VISION_MODEL": "gpt-4o-mini",
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
                "PINRAG_YT_VISION_PROVIDER": "openai",
                "PINRAG_YT_VISION_MODEL": "gpt-4o-mini",
                "PINRAG_YT_VISION_MAX_FRAMES": "2",
                "PINRAG_YT_VISION_MIN_SCENE_SCORE": "25",
            },
            clear=False,
        ):
            enriched = enrich_with_vision(load_result)

    assert len(enriched.documents) == len(load_result.documents)
    assert any(d.metadata.get("has_visual") for d in enriched.documents)


def test_parse_openrouter_video_segments_plain_json() -> None:
    raw = (
        '[{"start_s": 0, "end_s": 10, "description": "Terminal: npm install"}, '
        '{"start_s": 10, "end_s": 20, "description": "NO_CONTENT"}]'
    )
    out = _parse_openrouter_video_segments(raw)
    assert len(out) == 1
    assert out[0].timestamp == 5.0
    assert "npm install" in out[0].description


def test_parse_openrouter_video_segments_markdown_fence() -> None:
    raw = (
        '```json\n[{"start_s": 1, "end_s": 3, "description": "Slide title: Setup"}]\n```'
    )
    out = _parse_openrouter_video_segments(raw)
    assert len(out) == 1
    assert out[0].timestamp == 2.0


def test_analyze_frames_openrouter_empty_source_url() -> None:
    assert (
        analyze_frames(
            [],
            provider="openrouter",
            model="google/gemini-2.5-flash",
            source_url="",
        )
        == []
    )


@patch("openai.OpenAI")
@patch("pinrag.indexing.youtube_vision.extract_frames")
@patch("pinrag.indexing.youtube_vision.download_video")
def test_enrich_with_vision_openrouter_skips_download_and_sends_video_url(
    mock_download: MagicMock,
    mock_extract: MagicMock,
    mock_openai_cls: MagicMock,
) -> None:
    """OpenRouter path does not download or extract; one API call with video_url."""
    docs = _make_transcript_docs("vidopenrouter")
    load_result = YouTubeLoadResult(
        video_id="vidopenrouter",
        source_url="https://www.youtube.com/watch?v=vidopenrouter",
        documents=docs,
        total_segments=2,
        title="OR Vision",
    )
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content=(
                        '[{"start_s": 8, "end_s": 14, "description": "IDE shows main.c buffer"}]'
                    )
                )
            )
        ]
    )

    with patch.dict(
        os.environ,
        {
            "PINRAG_YT_VISION_PROVIDER": "openrouter",
            "PINRAG_YT_VISION_MODEL": "google/gemini-2.5-flash",
            "OPENROUTER_API_KEY": "test-key",
        },
        clear=False,
    ):
        enriched = enrich_with_vision(load_result)

    mock_download.assert_not_called()
    mock_extract.assert_not_called()
    mock_openai_cls.assert_called_once()
    call_kw = mock_client.chat.completions.create.call_args.kwargs
    content = call_kw["messages"][0]["content"]
    assert any(
        part.get("type") == "video_url"
        and part.get("video_url", {}).get("url") == load_result.source_url
        for part in content
    )
    assert call_kw["model"] == "google/gemini-2.5-flash"

    assert "main.c buffer" in enriched.documents[1].page_content
    assert enriched.documents[1].metadata.get("has_visual") is True


@patch("openai.OpenAI")
@patch("pinrag.indexing.youtube_vision.extract_frames")
@patch("pinrag.indexing.youtube_vision.download_video")
def test_enrich_with_vision_openrouter_bad_json_returns_unenriched(
    mock_download: MagicMock,
    mock_extract: MagicMock,
    mock_openai_cls: MagicMock,
) -> None:
    """Unparseable model output yields original documents (no merge)."""
    docs = _make_transcript_docs("badjsonvid")
    load_result = YouTubeLoadResult(
        video_id="badjsonvid",
        source_url="https://www.youtube.com/watch?v=badjsonvid",
        documents=docs,
        total_segments=2,
        title="Bad JSON",
    )
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="utter nonsense"))]
    )

    with patch.dict(
        os.environ,
        {
            "PINRAG_YT_VISION_PROVIDER": "openrouter",
            "OPENROUTER_API_KEY": "test-key",
        },
        clear=False,
    ):
        enriched = enrich_with_vision(load_result)

    mock_download.assert_not_called()
    mock_extract.assert_not_called()
    assert enriched.documents[0].page_content == load_result.documents[0].page_content
    assert not any(d.metadata.get("has_visual") for d in enriched.documents)


def test_fix_llm_json_repairs_unescaped_quotes() -> None:
    """_fix_llm_json escapes inner double quotes that break JSON parsing."""
    bad = (
        '[{"start_s": 0, "end_s": 10, '
        '"description": "Outputs "Hello, World!" on screen."}]'
    )
    import json

    with pytest.raises(json.JSONDecodeError):
        json.loads(bad)
    fixed = _fix_llm_json(bad)
    data = json.loads(fixed)
    assert len(data) == 1
    assert "Hello" in data[0]["description"]


def test_parse_openrouter_segments_handles_unescaped_quotes() -> None:
    """Parser recovers from unescaped quotes via _fix_llm_json fallback."""
    raw = (
        '```json\n'
        '[{"start_s": 5, "end_s": 15, '
        '"description": "Terminal shows "Hello, World!" output."}]\n'
        '```'
    )
    out = _parse_openrouter_video_segments(raw)
    assert len(out) == 1
    assert out[0].timestamp == 10.0
    assert "Hello" in out[0].description
