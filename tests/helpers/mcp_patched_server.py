"""Load ``pinrag.mcp.server`` with startup API-key validation patched off (test-only)."""

from __future__ import annotations

from unittest.mock import patch

with patch("pinrag.env_validation.require_api_keys_for_server", lambda: None):
    from pinrag.mcp import logging_utils as mcp_logging
    from pinrag.mcp import server as mcp_server

__all__ = ["mcp_logging", "mcp_server"]
