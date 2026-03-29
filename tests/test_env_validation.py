"""Unit tests for env_validation module."""

from __future__ import annotations

import pytest

from pinrag.env_validation import require_api_keys_for_server, require_llm_api_key


def test_require_llm_api_key_whitespace_only_key_exits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Whitespace-only ANTHROPIC_API_KEY is treated as missing."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", " ")
    with pytest.raises(SystemExit) as exc_info:
        require_llm_api_key()
    assert exc_info.value.code == 1


def test_require_api_keys_for_server_missing_llm_key_exits(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """require_api_keys_for_server exits when default OpenRouter LLM and OPENROUTER_API_KEY missing."""
    monkeypatch.delenv("PINRAG_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        require_api_keys_for_server()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "OPENROUTER_API_KEY" in err


def test_require_llm_api_key_anthropic_missing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """require_llm_api_key exits when provider=anthropic and ANTHROPIC_API_KEY not set."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        require_llm_api_key()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "mcp.json" in err


def test_require_llm_api_key_anthropic_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """require_llm_api_key does not exit when provider=anthropic and ANTHROPIC_API_KEY set."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    require_llm_api_key()


def test_require_llm_api_key_openai_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """require_llm_api_key exits when provider=openai and OPENAI_API_KEY not set."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        require_llm_api_key()
    assert exc_info.value.code == 1


def test_require_llm_api_key_openai_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """require_llm_api_key does not exit when provider=openai and OPENAI_API_KEY set."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    require_llm_api_key()


def test_require_llm_api_key_openrouter_missing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """require_llm_api_key exits when provider=openrouter and OPENROUTER_API_KEY not set."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openrouter")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        require_llm_api_key()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "OPENROUTER_API_KEY" in err


def test_require_llm_api_key_openrouter_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """require_llm_api_key does not exit when provider=openrouter and OPENROUTER_API_KEY set."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    require_llm_api_key()


def test_require_api_keys_for_server_defaults_exits_without_openrouter_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """require_api_keys_for_server exits when default OpenRouter LLM and OPENROUTER_API_KEY missing."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("PINRAG_LLM_PROVIDER", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        require_api_keys_for_server()
    assert exc_info.value.code == 1


def test_require_api_keys_for_server_defaults_passes_with_openrouter_key_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """require_api_keys_for_server passes when only OPENROUTER_API_KEY is set (default LLM)."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("PINRAG_LLM_PROVIDER", raising=False)
    require_api_keys_for_server()


def test_require_api_keys_for_server_openai_llm_passes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """require_api_keys_for_server passes when LLM=openai and OPENAI_API_KEY set."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    require_api_keys_for_server()
