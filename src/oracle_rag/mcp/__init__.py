"""MCP server for Oracle-RAG: exposes RAG tools via Model Context Protocol."""

from oracle_rag.mcp.server import create_mcp_server

__all__ = ["create_mcp_server"]
