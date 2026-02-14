"""OpenAI chat client for RAG. Reads OPENAI_API_KEY from env (or .env)."""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


DEFAULT_MODEL = "gpt-4o-mini"


def get_chat_model(
    *,
    model: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
    temperature: float = 0,
) -> ChatOpenAI:
    """Return an OpenAI chat model client.

    Loads .env so OPENAI_API_KEY can be set there. If api_key is passed, it
    overrides the environment variable.

    Args:
        model: OpenAI chat model name (default: gpt-4o-mini).
        api_key: Optional API key; otherwise uses OPENAI_API_KEY from env.
        temperature: Sampling temperature (default: 0 for deterministic).

    Returns:
        LangChain ChatOpenAI instance (invoke, stream, etc.).
    """
    load_dotenv()
    key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")
    return ChatOpenAI(model=model, api_key=key, temperature=temperature)
