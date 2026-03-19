"""Entry point script to run the PinRAG MCP server."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root so LangSmith and other vars are found
# even when Cursor (or another MCP client) starts the server with a different cwd.
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

# Validation runs when server module is imported
from pinrag.mcp.server import mcp  # noqa: E402


def main() -> None:
    """Run the MCP server with stdio transport."""
    # Run the server with stdio transport (standard for MCP clients)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
