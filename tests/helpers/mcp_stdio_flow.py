"""Shared MCP stdio tool sequence for integration tests (add → list → query → remove → list)."""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession
from mcp.types import CallToolResult

logger = logging.getLogger(__name__)


def parse_tool_result(result: CallToolResult) -> dict:
    assert not result.isError, result.content
    assert result.content, "empty tool result content"
    return json.loads(result.content[0].text)


async def run_amiga_pdf_stdio_flow(
    session: ClientSession,
    *,
    pdf_path: Path,
    query_text: str,
    log: logging.Logger | None = None,
    add_timeout: timedelta | None = None,
    query_timeout: timedelta | None = None,
    short_timeout: timedelta | None = None,
) -> None:
    """After ``session.initialize()``, run add/list/query/remove/list and assert."""
    log = log or logger
    add_timeout = add_timeout or timedelta(minutes=45)
    query_timeout = query_timeout or timedelta(minutes=15)
    short_timeout = short_timeout or timedelta(minutes=5)
    doc_id = pdf_path.name

    log.info(
        "call_tool add_document_tool paths=[%s] (timeout %s)",
        doc_id,
        add_timeout,
    )
    r_add = await session.call_tool(
        "add_document_tool",
        {"paths": [str(pdf_path)]},
        read_timeout_seconds=add_timeout,
    )
    data_add = parse_tool_result(r_add)
    log.info(
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

    log.info("call_tool list_documents_tool …")
    r_list = await session.call_tool(
        "list_documents_tool",
        {},
        read_timeout_seconds=short_timeout,
    )
    data_list = parse_tool_result(r_list)
    log.info(
        "list_documents_tool: %d document(s), %d chunk(s): %s",
        len(data_list.get("documents", [])),
        data_list.get("total_chunks", 0),
        data_list.get("documents"),
    )
    assert doc_id in data_list["documents"]
    assert data_list["total_chunks"] > 0

    log.info(
        "call_tool query_tool query=%r document_id=%s (timeout %s)",
        query_text,
        doc_id,
        query_timeout,
    )
    r_query = await session.call_tool(
        "query_tool",
        {
            "query": query_text,
            "document_id": doc_id,
        },
        read_timeout_seconds=query_timeout,
    )
    data_query = parse_tool_result(r_query)
    answer = (data_query.get("answer") or "").strip()
    sources = data_query.get("sources") or []
    log.info(
        "query_tool: answer_len=%d sources=%d (preview %.200s…)",
        len(answer),
        len(sources),
        answer.replace("\n", " "),
    )
    assert answer, "query_tool returned empty answer"
    assert any(
        str(s.get("document_id", "")) == doc_id for s in sources
    ), data_query

    log.info("call_tool remove_document_tool document_id=%s …", doc_id)
    r_rm = await session.call_tool(
        "remove_document_tool",
        {"document_id": doc_id},
        read_timeout_seconds=short_timeout,
    )
    data_rm = parse_tool_result(r_rm)
    log.info(
        "remove_document_tool: deleted_chunks=%s document_id=%s",
        data_rm.get("deleted_chunks"),
        data_rm.get("document_id"),
    )
    assert data_rm["deleted_chunks"] > 0
    assert data_rm["document_id"] == doc_id

    log.info("call_tool list_documents_tool (verify removal) …")
    r_list2 = await session.call_tool(
        "list_documents_tool",
        {},
        read_timeout_seconds=short_timeout,
    )
    data_list2 = parse_tool_result(r_list2)
    log.info(
        "list after remove: %d document(s), %s",
        len(data_list2.get("documents", [])),
        data_list2.get("documents"),
    )
    assert doc_id not in data_list2["documents"]
    log.info("MCP stdio integration flow steps completed OK")
