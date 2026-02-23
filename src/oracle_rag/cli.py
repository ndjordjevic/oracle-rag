"""CLI entry point for Oracle-RAG MCP server."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from oracle_rag.mcp.server import mcp


def _load_env() -> None:
    """Load .env from global config first, then cwd (cwd overrides)."""
    # Order: global first, then cwd — dotenv won't override, so cwd/.env takes precedence
    paths = [
        Path.home() / ".config" / "oracle-rag" / ".env",
        Path.home() / ".oracle-rag" / ".env",
        Path.cwd() / ".env",
    ]
    for p in paths:
        if p.exists():
            load_dotenv(p)
    # Also try default search (cwd and parents) for project-based usage
    load_dotenv()


def main() -> None:
    """Run the MCP server with stdio transport."""
    _load_env()

    if not os.environ.get("OPENAI_API_KEY"):
        print(
            "ERROR: OPENAI_API_KEY not set. Set it in .env (cwd or ~/.config/oracle-rag/) "
            "or in the environment.",
            file=sys.stderr,
        )
        sys.exit(1)

    mcp.run(transport="stdio")
