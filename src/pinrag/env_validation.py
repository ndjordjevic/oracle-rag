"""Startup validation for required API keys based on configured providers."""

from __future__ import annotations

import logging
import os
import sys

from pinrag.config import get_llm_provider

logger = logging.getLogger(__name__)

_ENV_HINT = (
    "Set it in the process environment—for Cursor/VS Code MCP, add keys under the "
    "server's `env` object in `mcp.json` (e.g. `~/.cursor/mcp.json` or `.vscode/mcp.json`). "
    "For CLI use, export the variable in your shell."
)

_LLM_KEYS = {
    "anthropic": ("ANTHROPIC_API_KEY", "PINRAG_LLM_PROVIDER"),
    "openai": ("OPENAI_API_KEY", "PINRAG_LLM_PROVIDER"),
    "openrouter": ("OPENROUTER_API_KEY", "PINRAG_LLM_PROVIDER"),
}


def _fail(key_env: str, provider_env: str, provider: str) -> None:
    """Log and print error, then exit."""
    msg = (
        f"{key_env} not set. It is required when {provider_env}={provider}. {_ENV_HINT}"
    )
    logger.error(msg)
    print(msg, file=sys.stderr)
    sys.exit(1)


def _require_key(
    provider: str,
    keys_map: dict[str, tuple[str, str]],
    valid_providers: str,
) -> None:
    """Check that the required API key for the given provider is set."""
    if provider not in keys_map:
        msg = f"Unknown provider: {provider}. Expected {valid_providers}."
        logger.error(msg)
        print(msg, file=sys.stderr)
        sys.exit(1)
    key_env, provider_env = keys_map[provider]
    raw = os.environ.get(key_env)
    if raw is None or not str(raw).strip():
        _fail(key_env, provider_env, provider)


def require_llm_api_key() -> None:
    """Verify the LLM provider's API key is set. Exit with error if missing."""
    provider = get_llm_provider()
    _require_key(provider, _LLM_KEYS, "anthropic, openai, or openrouter")


def require_api_keys_for_server() -> None:
    """Verify LLM API key is set. Exit with error if missing.

    Embeddings run locally (Nomic) and do not require an API key.
    """
    require_llm_api_key()
