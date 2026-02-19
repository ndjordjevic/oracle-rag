"""Entry point script to run the Oracle-RAG MCP server."""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

from oracle_rag.mcp.server import mcp

# Load environment variables
load_dotenv()

# Verify required environment variables
if not os.environ.get("OPENAI_API_KEY"):
    print(
        "ERROR: OPENAI_API_KEY not set. Set it in .env or the environment.",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    """Run the MCP server with stdio transport."""
    # Run the server with stdio transport (standard for MCP clients)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
