"""Tests for LLM (chat) client."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from pinrag.llm.openai_client import (
    DEFAULT_MODEL,
    get_chat_model,
    get_openai_chat_model,
)


def test_openai_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        get_openai_chat_model()


def test_openai_explicit_api_key_skips_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    llm = get_openai_chat_model(api_key="sk-from-arg")
    assert isinstance(llm, ChatOpenAI)


def test_get_chat_model_returns_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_chat_model returns ChatOpenAI when PINRAG_LLM_PROVIDER=openai."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("PINRAG_LLM_MODEL", DEFAULT_MODEL)
    llm = get_chat_model()
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == DEFAULT_MODEL


def test_get_chat_model_returns_anthropic_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_chat_model returns ChatAnthropic when PINRAG_LLM_PROVIDER=anthropic."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
    llm = get_chat_model()
    assert isinstance(llm, ChatAnthropic)


def test_chat_model_invoke(monkeypatch: pytest.MonkeyPatch) -> None:
    """invoke() returns string content (OpenAI path stubbed with a fake chat model)."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake")
    fake = FakeListChatModel(responses=["ok"])
    with patch("pinrag.llm.openai_client.ChatOpenAI", return_value=fake):
        llm = get_chat_model()
    response = llm.invoke([HumanMessage(content="Say 'ok' and nothing else.")])
    assert response.content
    assert isinstance(response.content, str)
    assert len(response.content.strip()) > 0
