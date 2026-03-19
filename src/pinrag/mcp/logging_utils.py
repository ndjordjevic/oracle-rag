"""Logging configuration and MCP tool notification helpers."""

from __future__ import annotations

import functools
import inspect
import logging
import os
import sys
import time
import warnings
from typing import Any

from mcp.server.fastmcp import Context
from mcp.server.fastmcp.utilities.context_injection import find_context_parameter

logger = logging.getLogger(__name__)


def _suppress_chroma_telemetry() -> None:
    """Disable Chroma telemetry to avoid PostHog INFO messages in Cursor Output."""
    os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")


def _configure_pinrag_logger() -> None:
    """Configure PinRAG root logger. By default, do not write to stderr because Cursor renders it with [error] badge."""
    log_to_stderr = (os.environ.get("PINRAG_LOG_TO_STDERR") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    level_name = (os.environ.get("PINRAG_LOG_LEVEL") or "INFO").strip().upper()
    level = getattr(logging, level_name, logging.INFO)
    if level_name not in ("DEBUG", "INFO", "WARNING", "ERROR"):
        level = logging.INFO

    root = logging.getLogger("pinrag")
    root.propagate = False
    root.setLevel(level)
    if log_to_stderr:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        if not root.handlers:
            root.addHandler(handler)
    else:
        root.setLevel(logging.CRITICAL + 1)


def _suppress_dependency_loggers() -> None:
    """Suppress verbose logs from dependencies that show as [error] in Cursor."""
    for name in ("mcp", "chromadb", "posthog", "openai", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore", message=".*Rotated text.*")


def configure_logging() -> None:
    """Configure PinRAG logging based on env vars. Call after .env is loaded."""
    _suppress_chroma_telemetry()
    _configure_pinrag_logger()
    _suppress_dependency_loggers()


def _user_friendly_api_error(exc: Exception) -> str | None:
    """Return a short, user-friendly message for API key / auth errors, or None."""
    msg = str(exc).lower()
    if "api key" in msg or "api_key" in msg or "authentication" in msg or "invalid key" in msg or "no api key" in msg:
        if "anthropic" in msg or "claude" in msg:
            return "Anthropic API key missing or invalid. Set ANTHROPIC_API_KEY in ~/.pinrag/.env (or your config)."
        if "cohere" in msg:
            return "Cohere API key missing or invalid. Set COHERE_API_KEY in ~/.pinrag/.env (or your config)."
        return "OpenAI API key not found or invalid. Set OPENAI_API_KEY in ~/.pinrag/.env (or your config)."
    if "rate" in msg and "limit" in msg:
        return "API rate limit exceeded. Please try again in a moment."
    return None


def _build_tool_summary(name: str, kwargs: dict[str, Any]) -> str:
    """Build a short summary string for tool logging. Always redacts sensitive content."""
    if name in ("add_document_tool", "add_url_tool"):
        paths = kwargs.get("paths", [])
        n = len(paths)
        if not paths:
            return "paths=[]"
        if n == 1:
            p = paths[0]
            preview = p[:60] + "..." if len(p) > 60 else p
            return f"paths={preview!r}"
        return f"paths={n} paths"
    if name == "query_tool":
        q = (kwargs.get("query") or "").strip()
        return f"query=<{len(q)} chars>" if q else "query=<empty>"
    if name == "list_documents_tool":
        return f"tag={kwargs.get('tag', '')!r}"
    if name == "remove_document_tool":
        return f"document_id={kwargs.get('document_id', '')!r}"
    return ""


async def _emit_client_log(ctx: Context | None, message: str, level: str = "info") -> None:
    """Best-effort tool log emission to MCP clients via notifications/message."""
    if ctx is None:
        return
    try:
        sender = getattr(ctx, level, None)
        if sender is None:
            await ctx.info(message)
            return
        await sender(message)
    except Exception:
        logger.debug("client_log_emit_failed level=%s message=%s", level, message, exc_info=True)


def _resolve_context_from_kwargs(fn: Any, kwargs: dict[str, Any]) -> Context | None:
    """Resolve Context from kwargs using annotation-based parameter lookup (FastMCP style)."""
    param_name = find_context_parameter(fn)
    if param_name is None:
        return None
    val = kwargs.get(param_name)
    return val if isinstance(val, Context) else None


def _log_tool_errors(fn):
    """Log tool entry, success, and errors to MCP clients via Context notifications.

    Preserves the wrapped function's signature so MCP/FastMCP schema introspection sees all parameters.
    """
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        summary = _build_tool_summary(fn.__name__, kwargs)
        ctx = _resolve_context_from_kwargs(fn, kwargs)
        start_msg = f"tool={fn.__name__} status=start {summary}".strip()
        await _emit_client_log(ctx, start_msg)
        start = time.perf_counter()
        try:
            result = await fn(*args, **kwargs)
            elapsed_s = time.perf_counter() - start
            await _emit_client_log(ctx, f"tool={fn.__name__} status=ok duration_s={elapsed_s:.2f}")
            return result
        except Exception as e:
            elapsed_s = time.perf_counter() - start
            await _emit_client_log(
                ctx,
                f"tool={fn.__name__} status=error duration_s={elapsed_s:.2f}",
                level="error",
            )
            friendly = _user_friendly_api_error(e)
            if friendly:
                raise RuntimeError(friendly) from e
            raise

    wrapper.__signature__ = inspect.signature(fn)
    wrapper.__annotations__ = fn.__annotations__
    return wrapper
