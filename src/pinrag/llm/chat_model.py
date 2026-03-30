"""Chat model client for RAG (OpenAI / Anthropic / OpenRouter)."""

from __future__ import annotations

import os
from importlib.util import find_spec

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from pinrag.config import (
    DEFAULT_LLM_MODEL_OPENAI,
    get_llm_model,
    get_llm_model_fallbacks,
    get_llm_provider,
    get_openrouter_app_title,
    get_openrouter_app_url,
    get_openrouter_provider_order,
    get_openrouter_sort,
)

# For tests and backward compatibility (OpenAI default model name).
DEFAULT_MODEL = DEFAULT_LLM_MODEL_OPENAI


def get_chat_model(
    *,
    model: str | None = None,
    api_key: str | None = None,
    temperature: float = 0,
) -> BaseChatModel:
    """Return a chat model based on PINRAG_LLM_PROVIDER (openai | anthropic | openrouter).

    For anthropic, requires ANTHROPIC_API_KEY and langchain-anthropic.
    For openai, requires OPENAI_API_KEY unless ``api_key`` is passed.
    For openrouter, requires OPENROUTER_API_KEY and langchain-openrouter.

    OpenRouter routing: optional ``PINRAG_OPENROUTER_MODEL_FALLBACKS``, ``PINRAG_OPENROUTER_SORT``,
    and ``PINRAG_OPENROUTER_PROVIDER_ORDER`` (``provider.order``; e.g. ``Cerebras`` for
    ``openai/gpt-oss-120b``) are read from the environment when the provider is openrouter.
    """
    provider = get_llm_provider()
    model_name = model if model is not None else get_llm_model()

    if provider == "openrouter":
        if find_spec("langchain_openrouter") is None:
            raise ImportError(
                "PINRAG_LLM_PROVIDER=openrouter requires langchain-openrouter. "
                "Install with: pip install langchain-openrouter"
            )
        from langchain_openrouter import ChatOpenRouter

        key = api_key if api_key is not None else os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("OPENROUTER_API_KEY is required for OpenRouter chat models.")
        fallbacks = get_llm_model_fallbacks()
        sort = get_openrouter_sort()
        order = get_openrouter_provider_order()
        model_kwargs = {"models": fallbacks} if fallbacks else {}
        provider_prefs: dict[str, object] = {}
        if sort:
            provider_prefs["sort"] = sort
        if order:
            provider_prefs["order"] = order
        openrouter_provider = provider_prefs if provider_prefs else None
        return ChatOpenRouter(  # type: ignore[call-arg]
            model=model_name,
            api_key=SecretStr(key),
            temperature=temperature,
            app_url=get_openrouter_app_url(),
            app_title=get_openrouter_app_title(),
            model_kwargs=model_kwargs,
            openrouter_provider=openrouter_provider,
        )

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
