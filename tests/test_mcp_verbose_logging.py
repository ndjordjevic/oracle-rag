"""Tests for verbose MCP notification helpers and phase emissions."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

from pinrag.indexing.youtube_indexer import YouTubeIndexResult
from pinrag.mcp import tools as mcp_tools
from tests.helpers.mcp_patched_server import mcp_logging


def test_emit_verbose_noop_when_disabled() -> None:
    """emit_verbose should no-op when PINRAG_VERBOSE_LOGGING is off."""
    ctx = MagicMock()
    with patch("pinrag.mcp.logging_utils.os.write") as mock_write:
        with patch(
            "pinrag.mcp.logging_utils.config.get_verbose_logging", return_value=False
        ):
            asyncio.run(mcp_logging.emit_verbose(ctx, "phase=disabled-test"))
    mock_write.assert_not_called()


def test_emit_verbose_writes_stderr_block_when_enabled() -> None:
    """emit_verbose should write a bordered block to fd 2."""
    ctx = MagicMock()
    msg = "phase=emit-test"
    with patch("pinrag.mcp.logging_utils.os.write") as mock_write:
        with patch(
            "pinrag.mcp.logging_utils.config.get_verbose_logging", return_value=True
        ):
            asyncio.run(mcp_logging.emit_verbose(ctx, msg))
    mock_write.assert_called_once()
    written = mock_write.call_args[0][1].decode()
    assert "pinrag verbose" in written
    assert msg in written
    assert "end verbose" in written


def test_collector_buffers_and_flushes_single_block() -> None:
    """VerboseCollector should buffer events and write one block on flush."""
    with patch("pinrag.mcp.logging_utils.os.write") as mock_write:
        with patch(
            "pinrag.mcp.logging_utils.config.get_verbose_logging", return_value=True
        ):
            collector = mcp_logging.VerboseCollector(scope="tool", name="test_tool")
            collector.emit("phase=a")
            collector.emit("phase=b")
            collector.emit("phase=c")
            mock_write.assert_not_called()
            collector.flush()
    mock_write.assert_called_once()
    written = mock_write.call_args[0][1].decode()
    assert "pinrag verbose" in written
    assert "tool=test_tool phase=a" in written
    assert "tool=test_tool phase=b" in written
    assert "tool=test_tool phase=c" in written
    assert "end verbose" in written


def test_collector_flush_noop_when_empty() -> None:
    """Flushing an empty collector should not write to stderr."""
    with patch("pinrag.mcp.logging_utils.os.write") as mock_write:
        with patch(
            "pinrag.mcp.logging_utils.config.get_verbose_logging", return_value=True
        ):
            collector = mcp_logging.VerboseCollector(scope="tool", name="test")
            collector.flush()
    mock_write.assert_not_called()


def test_make_verbose_emitter_returns_collector_backed_emitter() -> None:
    """make_verbose_emitter should return an emitter backed by a collector."""
    with patch(
        "pinrag.mcp.logging_utils.config.get_verbose_logging", return_value=True
    ):
        emitter = mcp_logging.make_verbose_emitter(
            MagicMock(), scope="tool", name="add_url_tool"
        )
        assert hasattr(emitter, "_collector")
        collector = emitter._collector  # type: ignore[attr-defined]
        with patch("pinrag.mcp.logging_utils.os.write") as mock_write:
            emitter("phase=step1")
            emitter("phase=step2")
            mock_write.assert_not_called()
            collector.flush()
        mock_write.assert_called_once()
        text = mock_write.call_args[0][1].decode()
        assert "phase=step1" in text
        assert "phase=step2" in text


def test_make_verbose_emitter_from_worker_thread() -> None:
    """Worker-thread emitter should collect events and flush as one block."""

    async def _run() -> None:
        ctx = MagicMock()
        with patch(
            "pinrag.mcp.logging_utils.config.get_verbose_logging", return_value=True
        ):
            emitter = mcp_logging.make_verbose_emitter(
                ctx, scope="tool", name="add_url_tool"
            )
            await asyncio.to_thread(emitter, "phase=a", "info")
            await asyncio.to_thread(emitter, "phase=b", "info")
            collector = emitter._collector  # type: ignore[attr-defined]
            with patch("pinrag.mcp.logging_utils.os.write") as mock_write:
                collector.flush()
            mock_write.assert_called_once()
            text = mock_write.call_args[0][1].decode()
            assert "phase=a" in text
            assert "phase=b" in text

    asyncio.run(_run())


def test_add_files_emits_verbose_phase_events() -> None:
    """add_files should emit verbose path lifecycle events."""
    events: list[tuple[str, str]] = []

    def _emit(message: str, level: str = "debug") -> None:
        events.append((message, level))

    fake_result = {"indexed": [{"path": "x"}], "failed": []}
    with patch("pinrag.mcp.tools.add_file", return_value=fake_result):
        mcp_tools.add_files(
            paths=["https://youtu.be/demo"],
            persist_dir="/tmp",
            collection="pinrag",
            verbose_emitter=_emit,
        )

    messages = [m for m, _ in events]
    assert any("phase=add_files_start" in m for m in messages)
    assert any("phase=add_files_path_start" in m for m in messages)
    assert any("phase=add_files_path_done" in m for m in messages)
    assert any("phase=add_files_done" in m for m in messages)


def test_add_file_youtube_emits_verbose_vision_related_phases() -> None:
    """add_file should emit youtube phase events and pass verbose emitter down."""
    events: list[tuple[str, str]] = []

    def _emit(message: str, level: str = "debug") -> None:
        events.append((message, level))

    fake_result = YouTubeIndexResult(
        video_id="abc123xyz00",
        source_url="https://www.youtube.com/watch?v=abc123xyz00",
        total_segments=12,
        total_chunks=16,
        persist_directory=mcp_tools.Path("/tmp"),
        collection_name="pinrag",
        title="Demo",
    )
    with patch("pinrag.mcp.tools._detect_source_format", return_value="youtube"):
        with patch("pinrag.mcp.tools.get_embedding_model", return_value=MagicMock()):
            with patch("pinrag.mcp.tools.index_youtube", return_value=fake_result):
                mcp_tools.add_file(
                    path="https://youtu.be/abc123xyz00",
                    persist_dir="/tmp",
                    collection="pinrag",
                    verbose_emitter=_emit,
                )

    messages = [m for m, _ in events]
    assert any("phase=detect_format" in m and "youtube" in m for m in messages)
    assert any("phase=youtube_index_start" in m for m in messages)
    assert any("phase=youtube_index_done" in m for m in messages)
