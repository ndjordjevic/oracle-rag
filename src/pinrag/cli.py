"""CLI entry point for PinRAG MCP server."""

from __future__ import annotations

import sys

from pinrag import __version__
from pinrag.env_validation import require_api_keys_for_server
from pinrag.mcp.server import configure_logging, mcp


def main() -> None:
    """Run the MCP server with stdio transport."""
    configure_logging()
    require_api_keys_for_server()
    sys.stderr.write(f"PinRAG MCP v{__version__}\n")
    mcp.run(transport="stdio")
