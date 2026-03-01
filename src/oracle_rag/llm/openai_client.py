"""OpenAI chat client for RAG. Reads OPENAI_API_KEY from env (or .env)."""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from oracle_rag.config import get_llm_model, get_llm_provider

DEFAULT_MODEL = "gpt-4o-mini"


def get_openai_chat_model(
    *,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0,
) -> ChatOpenAI:
    """Return an OpenAI chat model client.

    Loads .env so OPENAI_API_KEY can be set there. If api_key is passed, it
    overrides the environment variable.

    Args:
        model: OpenAI chat model name; if None, uses config (ORACLE_RAG_LLM_MODEL or gpt-4o-mini).
        api_key: Optional API key; otherwise uses OPENAI_API_KEY from env.
        temperature: Sampling temperature (default: 0 for deterministic).

    Returns:
        LangChain ChatOpenAI instance (invoke, stream, etc.).
    """
    load_dotenv()
    key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")
    model_name = model if model is not None else get_llm_model()
    return ChatOpenAI(model=model_name, api_key=key, temperature=temperature)


def get_chat_model(
    *,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0,
):
    """Return a chat model based on ORACLE_RAG_LLM_PROVIDER (openai | anthropic).

    For anthropic, requires ANTHROPIC_API_KEY and langchain-anthropic.
    For openai, requires OPENAI_API_KEY (default).
    """
    load_dotenv()
    provider = get_llm_provider()
    model_name = model if model is not None else get_llm_model()

    if provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as e:
            raise ImportError(
                "ORACLE_RAG_LLM_PROVIDER=anthropic requires langchain-anthropic. "
                "Install with: pip install langchain-anthropic"
            ) from e
        key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
        return ChatAnthropic(model=model_name, api_key=key, temperature=temperature)

    return get_openai_chat_model(model=model_name, api_key=api_key, temperature=temperature)
