"""CLI entry point for PinRAG MCP server."""

from __future__ import annotations

import os
import sys
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
    from pinrag.config import get_embedding_provider

    if get_embedding_provider() == "openai" and not os.environ.get("OPENAI_API_KEY"):
        print(
            "ERROR: OPENAI_API_KEY not set. It is required when PINRAG_EMBEDDING_PROVIDER=openai. "
            "Set it in .env (cwd or ~/.config/pinrag/) or in the environment.",
            file=sys.stderr,
        )
        sys.exit(1)

    from pinrag.mcp.server import mcp

    mcp.run(transport="stdio")
