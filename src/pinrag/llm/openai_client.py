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
    get_openrouter_sort,
    sync_openrouter_sdk_attribution_env,
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
        sync_openrouter_sdk_attribution_env()
        # app_url/app_title=None: SDK reads OPENROUTER_HTTP_REFERER / OPENROUTER_X_OPEN_ROUTER_TITLE
        # (set above); passing non-None would use langchain's x_title kwarg, which mismatches the SDK.
        fallbacks = get_llm_model_fallbacks()
        sort = get_openrouter_sort()
        model_kwargs = {"models": fallbacks} if fallbacks else {}
        openrouter_provider = {"sort": sort} if sort else None
        return ChatOpenRouter(  # type: ignore[call-arg]
            model=model_name,
            api_key=SecretStr(key),
            temperature=temperature,
            app_url=None,
            app_title=None,
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
