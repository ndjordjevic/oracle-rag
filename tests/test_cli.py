"""Unit tests for CLI entry point."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pinrag.cli import _load_env, main


def test_load_env_loads_from_cwd(tmp_path: Path) -> None:
    """_load_env calls load_dotenv for .env in cwd."""
    env_file = tmp_path / ".env"
    env_file.write_text("DUMMY=1")
    with patch("pinrag.cli.Path") as mock_path_cls:
        mock_home = MagicMock()
        cfg_env = MagicMock(exists=MagicMock(return_value=False))
        pinrag_env = MagicMock(exists=MagicMock(return_value=False))
        mock_home.__truediv__ = MagicMock(side_effect=lambda x: MagicMock(
            __truediv__=MagicMock(side_effect=lambda y: MagicMock(
                __truediv__=MagicMock(return_value=cfg_env),
                exists=MagicMock(return_value=False),
            )),
            exists=MagicMock(return_value=False),
        ))
        mock_path_cls.home.return_value = mock_home
        mock_path_cls.cwd.return_value = tmp_path
        with patch("pinrag.cli.load_dotenv") as mock_load:
            _load_env()
    mock_load.assert_called()


def test_main_exits_without_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() exits with code 1 when OPENAI_API_KEY is not set."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with patch("pinrag.cli._load_env"):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 1


def test_main_runs_mcp_server(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() imports and runs MCP server when required API keys are set."""
    # Default config: embedding=openai, LLM=anthropic — need both keys
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    mock_mcp = MagicMock()
    mock_module = MagicMock(mcp=mock_mcp)
    with patch("pinrag.cli._load_env"):
        with patch.dict("sys.modules", {"pinrag.mcp.server": mock_module}):
            main()
    mock_mcp.run.assert_called_once_with(transport="stdio")
