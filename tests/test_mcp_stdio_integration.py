"""Integration test: stdio MCP server (uv run pinrag-mcp) add → list → query → remove PDF.

API keys (required for the subprocess server):

1. ``OPENAI_API_KEY`` and ``ANTHROPIC_API_KEY`` in the process environment (e.g. CI secrets), or
2. Copy ``tests/mcp_stdio_integration.env.example`` to ``tests/.mcp_stdio_integration.env``
   and fill in keys (gitignored), or
3. Set ``PINRAG_MCP_ITEST_ENV_FILE`` to another ``KEY=value`` file path.

Environment variables win over the file for each key. Optional migration-only: set
``PINRAG_ITEST_USE_CURSOR_MCP_JSON=1`` to merge ``mcpServers.pinrag-dev.env`` from
``~/.cursor/mcp.json`` (deprecated).

Verbose progress: run pytest with ``--log-cli-level=INFO``, e.g.::

    pytest tests/test_mcp_stdio_integration.py -v -m integration --log-cli-level=INFO
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
from datetime import timedelta
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import CallToolResult

from tests.helpers.mcp_stdio_env import build_server_env_for_mcp_itest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_AMIGA_PDF = _REPO_ROOT / "data" / "pdfs" / "Bare-metal Amiga programming 2021_ocr.pdf"

_COLLECTION_ITEST = "pinrag_itest"
_QUERY_TEXT = "What's Amiga AGA?"

logger = logging.getLogger(__name__)


def _parse_tool_result(result: CallToolResult) -> dict:
    assert not result.isError, result.content
    assert result.content, "empty tool result content"
    return json.loads(result.content[0].text)


_SKIP_KEYS_HINT = (
    "Set OPENAI_API_KEY and ANTHROPIC_API_KEY in the environment, or copy "
    "tests/mcp_stdio_integration.env.example to tests/.mcp_stdio_integration.env, "
    "or set PINRAG_MCP_ITEST_ENV_FILE. Optional: PINRAG_ITEST_USE_CURSOR_MCP_JSON=1 "
    "to load keys from ~/.cursor/mcp.json pinrag-dev (deprecated)."
)


def _uv_bin() -> str | None:
    return os.environ.get("PINRAG_TEST_UV") or shutil.which("uv")


@pytest.mark.integration
def test_stdio_mcp_add_list_remove_pdf(tmp_path: Path) -> None:
    """Spawn pinrag-mcp via uv, index a PDF, list, query, remove; use isolated temp Chroma only."""
    chroma_dir = tmp_path / "chroma_itest"
    logger.info("Starting MCP stdio integration test")
    logger.info("Repo root: %s", _REPO_ROOT)
    logger.info("PDF path: %s (exists=%s)", _AMIGA_PDF, _AMIGA_PDF.is_file())

    env = build_server_env_for_mcp_itest(
        chroma_dir,
        collection_name=_COLLECTION_ITEST,
        test_file=Path(__file__),
    )

    if not env.get("OPENAI_API_KEY", "").strip():
        pytest.skip(f"OPENAI_API_KEY not set. {_SKIP_KEYS_HINT}")
    if not env.get("ANTHROPIC_API_KEY", "").strip():
        pytest.skip(f"ANTHROPIC_API_KEY not set. {_SKIP_KEYS_HINT}")
    if not _AMIGA_PDF.is_file():
        pytest.skip("Amiga PDF not present")
    uv_bin = _uv_bin()
    if not uv_bin:
        pytest.skip("uv not found (install uv or set PINRAG_TEST_UV)")
    logger.info("uv binary: %s", uv_bin)

    async def _run() -> None:
        params = StdioServerParameters(
            command=uv_bin,
            args=["run", "--project", str(_REPO_ROOT), "pinrag-mcp"],
            env=env,
        )
        logger.info(
            "Spawning MCP server: %s %s",
            params.command,
            " ".join(params.args or []),
        )
        add_timeout = timedelta(minutes=45)
        query_timeout = timedelta(minutes=15)
        short_timeout = timedelta(minutes=5)
        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    logger.info(
                        "Connecting stdio client; calling session.initialize() …"
                    )
                    await session.initialize()
                    logger.info("MCP session initialized (protocol handshake done)")

                    logger.info(
                        "call_tool add_document_tool paths=[%s] (timeout %s)",
                        _AMIGA_PDF.name,
                        add_timeout,
                    )
                    r_add = await session.call_tool(
                        "add_document_tool",
                        {"paths": [str(_AMIGA_PDF)]},
                        read_timeout_seconds=add_timeout,
                    )
                    data_add = _parse_tool_result(r_add)
                    logger.info(
                        "add_document_tool result: total_indexed=%s total_failed=%s "
                        "persist=%s collection=%s",
                        data_add.get("total_indexed"),
                        data_add.get("total_failed"),
                        data_add.get("persist_directory"),
                        data_add.get("collection_name"),
                    )
                    assert data_add["total_failed"] == 0, data_add
                    assert data_add["total_indexed"] >= 1
                    assert data_add["indexed"][0]["format"] == "pdf"
                    assert data_add["indexed"][0]["total_pages"] > 0

                    logger.info("call_tool list_documents_tool …")
                    r_list = await session.call_tool(
                        "list_documents_tool",
                        {},
                        read_timeout_seconds=short_timeout,
                    )
                    data_list = _parse_tool_result(r_list)
                    logger.info(
                        "list_documents_tool: %d document(s), %d chunk(s): %s",
                        len(data_list.get("documents", [])),
                        data_list.get("total_chunks", 0),
                        data_list.get("documents"),
                    )
                    assert _AMIGA_PDF.name in data_list["documents"]
                    assert data_list["total_chunks"] > 0

                    logger.info(
                        "call_tool query_tool query=%r document_id=%s (timeout %s)",
                        _QUERY_TEXT,
                        _AMIGA_PDF.name,
                        query_timeout,
                    )
                    r_query = await session.call_tool(
                        "query_tool",
                        {
                            "query": _QUERY_TEXT,
                            "document_id": _AMIGA_PDF.name,
                        },
                        read_timeout_seconds=query_timeout,
                    )
                    data_query = _parse_tool_result(r_query)
                    answer = (data_query.get("answer") or "").strip()
                    sources = data_query.get("sources") or []
                    logger.info(
                        "query_tool: answer_len=%d sources=%d (preview %.200s…)",
                        len(answer),
                        len(sources),
                        answer.replace("\n", " "),
                    )
                    assert answer, "query_tool returned empty answer"
                    assert any(
                        str(s.get("document_id", "")) == _AMIGA_PDF.name
                        for s in sources
                    ), data_query

                    logger.info(
                        "call_tool remove_document_tool document_id=%s …",
                        _AMIGA_PDF.name,
                    )
                    r_rm = await session.call_tool(
                        "remove_document_tool",
                        {"document_id": _AMIGA_PDF.name},
                        read_timeout_seconds=short_timeout,
                    )
                    data_rm = _parse_tool_result(r_rm)
                    logger.info(
                        "remove_document_tool: deleted_chunks=%s document_id=%s",
                        data_rm.get("deleted_chunks"),
                        data_rm.get("document_id"),
                    )
                    assert data_rm["deleted_chunks"] > 0
                    assert data_rm["document_id"] == _AMIGA_PDF.name

                    logger.info("call_tool list_documents_tool (verify removal) …")
                    r_list2 = await session.call_tool(
                        "list_documents_tool",
                        {},
                        read_timeout_seconds=short_timeout,
                    )
                    data_list2 = _parse_tool_result(r_list2)
                    logger.info(
                        "list after remove: %d document(s), %s",
                        len(data_list2.get("documents", [])),
                        data_list2.get("documents"),
                    )
                    assert _AMIGA_PDF.name not in data_list2["documents"]
                    logger.info("MCP stdio integration test steps completed OK")
        finally:
            logger.info("Removing temp chroma dir: %s", chroma_dir)
            shutil.rmtree(chroma_dir, ignore_errors=True)

    asyncio.run(_run())
