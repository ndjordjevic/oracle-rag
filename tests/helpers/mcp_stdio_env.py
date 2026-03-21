"""Env loading for MCP stdio integration tests (no python-dotenv dependency)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_API_KEYS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY")
_MCP_JSON = Path.home() / ".cursor" / "mcp.json"


def truthy_env(name: str) -> bool:
    """Return True if env var is set to 1, true, or yes (case-insensitive)."""
    return (os.environ.get(name) or "").strip().lower() in ("1", "true", "yes")


def resolve_mcp_itest_env_file_path(test_file: Path) -> Path:
    """Path to secrets file: PINRAG_MCP_ITEST_ENV_FILE or tests/.mcp_stdio_integration.env."""
    override = (os.environ.get("PINRAG_MCP_ITEST_ENV_FILE") or "").strip()
    if override:
        p = Path(override).expanduser()
        if not p.is_absolute():
            p = (Path.cwd() / p).resolve()
        return p
    return (test_file.resolve().parent / ".mcp_stdio_integration.env").resolve()


def load_optional_env_file(path: Path) -> dict[str, str]:
    """Parse KEY=value lines; only OPENAI_API_KEY and ANTHROPIC_API_KEY are returned."""
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key in _API_KEYS:
            out[key] = val
    return out


def merge_cursor_pinrag_dev(env: dict[str, str]) -> dict[str, str]:
    """Merge mcpServers.pinrag-dev.env from ~/.cursor/mcp.json into env (mutates env)."""
    try:
        mcp_cfg = json.loads(_MCP_JSON.read_text(encoding="utf-8"))
        cursor_env = mcp_cfg.get("mcpServers", {}).get("pinrag-dev", {}).get("env", {})
        for k, v in cursor_env.items():
            env[str(k)] = str(v)
        logger.info(
            "Merged env from %s (mcpServers.pinrag-dev.env: %d keys)",
            _MCP_JSON,
            len(cursor_env),
        )
        return dict(cursor_env)
    except (OSError, json.JSONDecodeError, TypeError) as e:
        logger.warning(
            "PINRAG_ITEST_USE_CURSOR_MCP_JSON set but could not read %s (%s: %s)",
            _MCP_JSON,
            type(e).__name__,
            e,
        )
        return {}


def build_server_env_for_mcp_itest(
    chroma_dir: Path,
    *,
    collection_name: str,
    test_file: Path,
) -> dict[str, str]:
    """Build subprocess env: os.environ, optional file gaps, optional Cursor merge, storage overrides."""
    env: dict[str, str] = {k: str(v) for k, v in os.environ.items()}
    source: dict[str, str] = {}

    for k in _API_KEYS:
        if env.get(k, "").strip():
            source[k] = "env"

    env_path = resolve_mcp_itest_env_file_path(test_file)
    file_vals = load_optional_env_file(env_path)
    if env_path.is_file():
        logger.info("MCP stdio integration test env file present: %s", env_path)
    for k in _API_KEYS:
        if not env.get(k, "").strip() and file_vals.get(k, "").strip():
            env[k] = file_vals[k]
            source[k] = "file"

    if truthy_env("PINRAG_ITEST_USE_CURSOR_MCP_JSON"):
        cursor_env = merge_cursor_pinrag_dev(env)
        for k in _API_KEYS:
            if k in cursor_env:
                source[k] = "cursor"

    env["PINRAG_PERSIST_DIR"] = str(chroma_dir)
    env["PINRAG_COLLECTION_NAME"] = collection_name

    logger.info(
        "Storage override: PINRAG_PERSIST_DIR=%s PINRAG_COLLECTION_NAME=%s",
        chroma_dir,
        collection_name,
    )
    for k in _API_KEYS:
        logger.info(
            "%s: %s (from %s)",
            k,
            "set" if env.get(k, "").strip() else "absent",
            source.get(k, "n/a"),
        )
    return env
