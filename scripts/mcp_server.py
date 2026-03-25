"""Dev entry: run the PinRAG MCP server from a git checkout.

Same wire protocol as the packaged ``pinrag`` console script. Environment
variables are not loaded from any file — set them in MCP ``env`` or export
in your shell before running.
"""

from __future__ import annotations

from pinrag.mcp.server import mcp


def main() -> None:
    """Run the MCP server with stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
