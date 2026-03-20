"""Unit tests for env_validation module."""

from __future__ import annotations

import pytest

from pinrag.env_validation import (
    require_api_keys_for_server,
    require_embedding_api_key,
    require_llm_api_key,
)


def test_require_embedding_api_key_openai_missing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """require_embedding_api_key exits when provider=openai and OPENAI_API_KEY not set."""
    monkeypatch.setenv("PINRAG_EMBEDDING_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("COHERE_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        require_embedding_api_key()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "mcp.json" in err


def test_require_embedding_api_key_openai_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """require_embedding_api_key does not exit when provider=openai and OPENAI_API_KEY set."""
    monkeypatch.setenv("PINRAG_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    require_embedding_api_key()


def test_require_embedding_api_key_openai_empty_string_exits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty OPENAI_API_KEY is treated as missing."""
    monkeypatch.setenv("PINRAG_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    with pytest.raises(SystemExit) as exc_info:
        require_embedding_api_key()
    assert exc_info.value.code == 1


def test_require_embedding_api_key_openai_whitespace_only_exits(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Whitespace-only OPENAI_API_KEY is treated as missing."""
    monkeypatch.setenv("PINRAG_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "   \t  ")
    with pytest.raises(SystemExit) as exc_info:
        require_embedding_api_key()
    assert exc_info.value.code == 1
    assert "OPENAI_API_KEY" in capsys.readouterr().err


def test_require_llm_api_key_whitespace_only_key_exits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Whitespace-only ANTHROPIC_API_KEY is treated as missing."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", " ")
    with pytest.raises(SystemExit) as exc_info:
        require_llm_api_key()
    assert exc_info.value.code == 1


def test_require_embedding_api_key_unknown_provider_exits(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Unknown embedding provider from config triggers exit (defensive if maps diverge)."""
    monkeypatch.setattr(
        "pinrag.env_validation.get_embedding_provider", lambda: "unknown-vendor"
    )
    with pytest.raises(SystemExit) as exc_info:
        require_embedding_api_key()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "Unknown provider" in err
    assert "openai or cohere" in err


def test_require_api_keys_for_server_checks_embedding_before_llm(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """With default providers, missing embedding key fails before LLM key is considered."""
    monkeypatch.delenv("PINRAG_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("PINRAG_EMBEDDING_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-only")
    with pytest.raises(SystemExit) as exc_info:
        require_api_keys_for_server()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "OPENAI_API_KEY" in err
    assert "PINRAG_EMBEDDING_PROVIDER" in err


def test_require_embedding_api_key_cohere_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """require_embedding_api_key exits when provider=cohere and COHERE_API_KEY not set."""
    monkeypatch.setenv("PINRAG_EMBEDDING_PROVIDER", "cohere")
    monkeypatch.delenv("COHERE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        require_embedding_api_key()
    assert exc_info.value.code == 1


def test_require_embedding_api_key_cohere_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """require_embedding_api_key does not exit when provider=cohere and COHERE_API_KEY set."""
    monkeypatch.setenv("PINRAG_EMBEDDING_PROVIDER", "cohere")
    monkeypatch.setenv("COHERE_API_KEY", "test-cohere-key")
    require_embedding_api_key()


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


def test_require_api_keys_for_server_defaults_exits_without_both(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """require_api_keys_for_server exits when defaults (anthropic LLM, openai embedding) and keys missing."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("PINRAG_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("PINRAG_EMBEDDING_PROVIDER", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        require_api_keys_for_server()
    assert exc_info.value.code == 1


def test_require_api_keys_for_server_defaults_passes_with_both(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """require_api_keys_for_server passes when defaults and both keys set."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    require_api_keys_for_server()


def test_require_api_keys_for_server_openai_only_passes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """require_api_keys_for_server passes when both providers=openai and OPENAI_API_KEY set."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openai")
    monkeypatch.setenv("PINRAG_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    require_api_keys_for_server()
