"""CLI entry point for PinRAG MCP server."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def _load_env() -> None:
    """Load .env from well-known paths before any other imports touch env vars."""
    paths = [
        Path.home() / ".config" / "pinrag" / ".env",
        Path.home() / ".pinrag" / ".env",
        Path.cwd() / ".env",
    ]
    for p in paths:
        if p.exists():
            load_dotenv(p)
    load_dotenv()


def main() -> None:
    """Run the MCP server with stdio transport."""
    _load_env()
    from pinrag.env_validation import require_api_keys_for_server

    require_api_keys_for_server()

    from pinrag.mcp.server import mcp

    mcp.run(transport="stdio")
