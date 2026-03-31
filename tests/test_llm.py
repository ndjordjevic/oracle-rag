"""Tests for LLM (chat) client."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_openrouter import ChatOpenRouter

from pinrag.config import (
    DEFAULT_CEREBRAS_BASE_URL,
    DEFAULT_LLM_MODEL_CEREBRAS,
    DEFAULT_LLM_MODEL_OPENROUTER,
    DEFAULT_OPENROUTER_APP_TITLE,
    DEFAULT_OPENROUTER_APP_URL,
)
from pinrag.llm.chat_model import DEFAULT_MODEL, get_chat_model


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


def test_cerebras_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "cerebras")
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    with pytest.raises(ValueError, match="CEREBRAS_API_KEY"):
        get_chat_model()


def test_cerebras_explicit_api_key_skips_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "cerebras")
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    llm = get_chat_model(api_key="cb-from-arg")
    assert isinstance(llm, ChatOpenAI)


def test_get_chat_model_returns_cerebras_chat_openai(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_chat_model returns ChatOpenAI with Cerebras base URL when provider=cerebras."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "cerebras")
    monkeypatch.setenv("CEREBRAS_API_KEY", "cb-test-key")
    monkeypatch.delenv("PINRAG_LLM_MODEL", raising=False)
    llm = get_chat_model()
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == DEFAULT_LLM_MODEL_CEREBRAS
    assert llm.openai_api_base == DEFAULT_CEREBRAS_BASE_URL.rstrip("/")


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
    monkeypatch.delenv("PINRAG_OPENROUTER_MODEL_FALLBACKS", raising=False)
    monkeypatch.delenv("PINRAG_LLM_MODEL_FALLBACKS", raising=False)
    monkeypatch.delenv("PINRAG_OPENROUTER_SORT", raising=False)
    monkeypatch.delenv("PINRAG_OPENROUTER_PROVIDER_ORDER", raising=False)
    llm = get_chat_model()
    assert isinstance(llm, ChatOpenRouter)
    assert llm.model_name == DEFAULT_LLM_MODEL_OPENROUTER
    assert llm.app_url == DEFAULT_OPENROUTER_APP_URL
    assert llm.app_title == DEFAULT_OPENROUTER_APP_TITLE


def test_openrouter_model_fallbacks_and_sort_in_chat_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenRouter extras: PINRAG_OPENROUTER_MODEL_FALLBACKS and PINRAG_OPENROUTER_SORT."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")
    monkeypatch.setenv("PINRAG_LLM_MODEL", "openrouter/free")
    monkeypatch.delenv("PINRAG_LLM_MODEL_FALLBACKS", raising=False)
    monkeypatch.delenv("PINRAG_OPENROUTER_PROVIDER_ORDER", raising=False)
    monkeypatch.setenv(
        "PINRAG_OPENROUTER_MODEL_FALLBACKS",
        "meta/llama:free, google/gemini:free",
    )
    monkeypatch.setenv("PINRAG_OPENROUTER_SORT", "throughput")
    llm = get_chat_model()
    assert isinstance(llm, ChatOpenRouter)
    assert llm.model_kwargs == {"models": ["meta/llama:free", "google/gemini:free"]}
    assert llm.openrouter_provider == {"sort": "throughput"}


def test_openrouter_provider_order_in_chat_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PINRAG_OPENROUTER_PROVIDER_ORDER maps to ChatOpenRouter openrouter_provider.order."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")
    monkeypatch.setenv("PINRAG_LLM_MODEL", "openai/gpt-oss-120b")
    monkeypatch.delenv("PINRAG_OPENROUTER_MODEL_FALLBACKS", raising=False)
    monkeypatch.delenv("PINRAG_LLM_MODEL_FALLBACKS", raising=False)
    monkeypatch.delenv("PINRAG_OPENROUTER_SORT", raising=False)
    monkeypatch.setenv("PINRAG_OPENROUTER_PROVIDER_ORDER", "Cerebras")
    llm = get_chat_model()
    assert isinstance(llm, ChatOpenRouter)
    assert llm.openrouter_provider == {"order": ["Cerebras"]}


def test_openrouter_fallbacks_sort_and_provider_order_in_chat_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenRouter provider dict merges sort and order with model fallbacks."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")
    monkeypatch.setenv("PINRAG_LLM_MODEL", "openai/gpt-oss-120b")
    monkeypatch.setenv("PINRAG_OPENROUTER_MODEL_FALLBACKS", "meta/llama:free")
    monkeypatch.setenv("PINRAG_OPENROUTER_SORT", "latency")
    monkeypatch.setenv("PINRAG_OPENROUTER_PROVIDER_ORDER", "Cerebras,Other")
    llm = get_chat_model()
    assert isinstance(llm, ChatOpenRouter)
    assert llm.model_kwargs == {"models": ["meta/llama:free"]}
    assert llm.openrouter_provider == {
        "sort": "latency",
        "order": ["Cerebras", "Other"],
    }


def test_openrouter_app_attribution_override_in_chat_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PINRAG_OPENROUTER_PROVIDER_ORDER", raising=False)
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")
    monkeypatch.setenv("OPENROUTER_APP_URL", "https://custom.example")
    monkeypatch.setenv("OPENROUTER_APP_TITLE", "MyPinRAG")
    llm = get_chat_model()
    assert isinstance(llm, ChatOpenRouter)
    assert llm.app_url == "https://custom.example"
    assert llm.app_title == "MyPinRAG"


def test_chat_model_invoke(monkeypatch: pytest.MonkeyPatch) -> None:
    """invoke() returns string content (OpenAI path stubbed with a fake chat model)."""
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake")
    fake = FakeListChatModel(responses=["ok"])
    with patch("pinrag.llm.chat_model.ChatOpenAI", return_value=fake):
        llm = get_chat_model()
    response = llm.invoke([HumanMessage(content="Say 'ok' and nothing else.")])
    assert response.content
    assert isinstance(response.content, str)
    assert len(response.content.strip()) > 0
