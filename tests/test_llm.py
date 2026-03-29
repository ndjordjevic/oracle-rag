"""Tests for LLM (chat) client."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_openrouter import ChatOpenRouter

from pinrag.config import (
    DEFAULT_LLM_MODEL_OPENROUTER,
    DEFAULT_OPENROUTER_APP_TITLE,
    DEFAULT_OPENROUTER_APP_URL,
)
from pinrag.llm.openai_client import DEFAULT_MODEL, get_chat_model


def test_openai_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        get_chat_model()


def test_openai_explicit_api_key_skips_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    llm = get_chat_model(api_key="sk-from-arg")
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


def test_openrouter_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openrouter")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        get_chat_model()


def test_openrouter_explicit_api_key_skips_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openrouter")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    llm = get_chat_model(api_key="sk-or-from-arg")
    assert isinstance(llm, ChatOpenRouter)


def test_get_chat_model_returns_openrouter_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_chat_model returns ChatOpenRouter when PINRAG_LLM_PROVIDER=openrouter."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")
    monkeypatch.setenv("PINRAG_LLM_MODEL", DEFAULT_LLM_MODEL_OPENROUTER)
    llm = get_chat_model()
    assert isinstance(llm, ChatOpenRouter)
    assert llm.model_name == DEFAULT_LLM_MODEL_OPENROUTER
    assert os.environ.get("OPENROUTER_HTTP_REFERER") == DEFAULT_OPENROUTER_APP_URL
    assert os.environ.get("OPENROUTER_X_OPEN_ROUTER_TITLE") == DEFAULT_OPENROUTER_APP_TITLE


def test_openrouter_app_attribution_env_override_in_chat_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")
    monkeypatch.setenv("OPENROUTER_APP_URL", "https://custom.example")
    monkeypatch.setenv("OPENROUTER_APP_TITLE", "MyPinRAG")
    llm = get_chat_model()
    assert isinstance(llm, ChatOpenRouter)
    assert os.environ.get("OPENROUTER_HTTP_REFERER") == "https://custom.example"
    assert os.environ.get("OPENROUTER_X_OPEN_ROUTER_TITLE") == "MyPinRAG"


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
