"""Unit tests for CLI entry point."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pinrag.cli import main


def test_main_exits_without_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() exits with code 1 when OPENAI_API_KEY is not set."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_runs_mcp_server(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() runs MCP server when required API keys are set."""
    # Default config: embedding=openai, LLM=anthropic — need both keys
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    mock_mcp = MagicMock()
    with patch("pinrag.cli.configure_logging"):
        with patch("pinrag.cli.mcp", mock_mcp):
            main()
    mock_mcp.run.assert_called_once_with(transport="stdio")
