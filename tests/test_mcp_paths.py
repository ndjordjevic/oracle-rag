"""Tests for path resolution helpers in MCP tools."""

from __future__ import annotations

import pytest

from pinrag.mcp.tools import (
    _resolve_persist_dir_path,
    _resolve_user_content_path,
)


def test_resolve_user_content_path_rejects_parent_segments() -> None:
    with pytest.raises(ValueError, match="parent directory"):
        _resolve_user_content_path("/tmp/../etc/passwd")


def test_resolve_user_content_path_rejects_null_byte() -> None:
    with pytest.raises(ValueError, match="null"):
        _resolve_user_content_path("/tmp/foo\x00/bar")


def test_resolve_persist_dir_path_rejects_null_byte() -> None:
    with pytest.raises(ValueError, match="null"):
        _resolve_persist_dir_path("/tmp/foo\x00/bar")


def test_resolve_persist_dir_path_allows_parent_segments(tmp_path) -> None:
    """Config paths may use .. after expanduser; persist dir is trusted user config."""
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    p = str(tmp_path / "a" / ".." / "a" / "b")
    resolved = _resolve_persist_dir_path(p)
    assert resolved == sub.resolve()
