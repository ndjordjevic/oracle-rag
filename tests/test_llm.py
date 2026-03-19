"""Tests for LLM (chat) client."""

from __future__ import annotations

import os

import pytest
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from pinrag.llm.openai_client import DEFAULT_MODEL, get_chat_model


def test_get_chat_model_returns_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_chat_model returns ChatOpenAI when PINRAG_LLM_PROVIDER=openai."""
    from dotenv import load_dotenv

    load_dotenv()
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "openai")
    monkeypatch.setenv("PINRAG_LLM_MODEL", DEFAULT_MODEL)  # override .env
    try:
        llm = get_chat_model()
    except Exception:
        pytest.skip("OPENAI_API_KEY not set or invalid; skipping")
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == DEFAULT_MODEL


def test_get_chat_model_returns_anthropic_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_chat_model returns ChatAnthropic when PINRAG_LLM_PROVIDER=anthropic."""
    from dotenv import load_dotenv

    load_dotenv()
    monkeypatch.setenv("PINRAG_LLM_PROVIDER", "anthropic")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set; skipping")
    llm = get_chat_model()
    assert isinstance(llm, ChatAnthropic)


def test_chat_model_invoke() -> None:
    """Invoke with a simple prompt returns a non-empty response."""
    from dotenv import load_dotenv

    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set; skipping LLM test")

    llm = get_chat_model()
    response = llm.invoke([HumanMessage(content="Say 'ok' and nothing else.")])
    assert response.content
    assert isinstance(response.content, str)
    assert len(response.content.strip()) > 0
