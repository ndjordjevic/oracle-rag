"""Chat model client for RAG (OpenAI / Anthropic)."""

from __future__ import annotations

import os
from importlib.util import find_spec

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from pinrag.config import DEFAULT_LLM_MODEL_OPENAI, get_llm_model, get_llm_provider

# For tests and backward compatibility.
DEFAULT_MODEL = DEFAULT_LLM_MODEL_OPENAI


def get_chat_model(
    *,
    model: str | None = None,
    api_key: str | None = None,
    temperature: float = 0,
) -> BaseChatModel:
    """Return a chat model based on PINRAG_LLM_PROVIDER (openai | anthropic).

    For anthropic, requires ANTHROPIC_API_KEY and langchain-anthropic.
    For openai, requires OPENAI_API_KEY unless ``api_key`` is passed.
    """
    provider = get_llm_provider()
    model_name = model if model is not None else get_llm_model()

    if provider == "anthropic":
        if find_spec("langchain_anthropic") is None:
            raise ImportError(
                "PINRAG_LLM_PROVIDER=anthropic requires langchain-anthropic. "
                "Install with: pip install langchain-anthropic"
            )
        from langchain_anthropic import ChatAnthropic

        key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic chat models.")
        return ChatAnthropic(  # type: ignore[call-arg]
            model_name=model_name,
            api_key=SecretStr(key),
            temperature=temperature,
        )

    key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY is required for OpenAI chat models.")
    return ChatOpenAI(
        model=model_name, api_key=SecretStr(key), temperature=temperature
    )
