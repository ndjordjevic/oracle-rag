"""MCP server for PinRAG: exposes RAG tools via Model Context Protocol."""

from pinrag.mcp.server import create_mcp_server

__all__ = ["create_mcp_server"]
