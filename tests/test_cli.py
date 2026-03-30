"""Unit tests for CLI entry point."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pinrag.cli import main


def test_main_exits_without_llm_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() exits with code 1 when OPENROUTER_API_KEY is not set (default LLM provider)."""
    monkeypatch.delenv("PINRAG_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_runs_mcp_server(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() runs MCP server when required API keys are set."""
    # Default LLM is openrouter — set OPENROUTER_API_KEY (or use openai + OPENAI_API_KEY).
    monkeypatch.delenv("PINRAG_LLM_PROVIDER", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    mock_mcp = MagicMock()
    with patch("pinrag.cli.configure_logging"):
        with patch("pinrag.cli.mcp", mock_mcp):
            with patch("pinrag.cli.__version__", "9.9.9-test"):
                with patch("pinrag.cli.sys.stderr") as mock_stderr:
                    main()
    mock_mcp.run.assert_called_once_with(transport="stdio")
    mock_stderr.write.assert_called_once_with("PinRAG MCP v9.9.9-test\n")
    mock_stderr.flush.assert_called_once()
