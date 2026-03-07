"""MCP server setup using FastMCP."""

from __future__ import annotations

import functools
import logging
import os
import sys

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from oracle_rag.config import get_collection_name, get_persist_dir
from oracle_rag.mcp.tools import (
    add_file,
    add_files,
    list_documents,
    query as query_index,
    remove_document,
)

# Load environment variables
load_dotenv()

# Disable Chroma telemetry — avoids PostHog INFO messages in Cursor Output
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

# Configure logging to stderr so it appears in Cursor's Output panel for this MCP
_log_handler = logging.StreamHandler(sys.stderr)
_log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
_log = logging.getLogger("oracle_rag.mcp")
_log.setLevel(logging.INFO)
_log.propagate = False
if not _log.handlers:
    _log.addHandler(_log_handler)

# Suppress verbose INFO logs from dependencies — they go to stderr and show as [error] in Cursor
for _name in ("mcp", "chromadb", "posthog", "openai", "httpx", "httpcore"):
    logging.getLogger(_name).setLevel(logging.WARNING)
# pypdf logs "Rotated text discovered" at WARNING level — suppress entirely
logging.getLogger("pypdf").setLevel(logging.ERROR)
# pypdf also uses warnings module for "Rotated text discovered"
import warnings
warnings.filterwarnings("ignore", message=".*Rotated text.*")

# Verify required environment variables
if not os.environ.get("OPENAI_API_KEY"):
    _log.warning("OPENAI_API_KEY not set. MCP tools will fail without it.")

# Create FastMCP server instance
mcp = FastMCP("Oracle-RAG", json_response=True)


def _log_tool_errors(fn):
    """Decorator: log exceptions to stderr (Cursor Output) then re-raise so client gets the error."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            _log.exception("Tool %s failed", fn.__name__)
            raise

    return wrapper


@mcp.tool()
@_log_tool_errors
def query_tool(
    query: str,
    k: int = 5,
    persist_dir: str = "",
    collection: str = "oracle_rag",
    document_id: str = "",
    page_min: int | None = None,
    page_max: int | None = None,
    tag: str = "",
) -> dict:
    """Query indexed documents and return an answer with citations.

    Searches through all indexed documents (PDF, Discord, etc.) and uses RAG
    to provide an answer based on retrieved context, with source citations.

    Args:
        query: Natural language question to ask.
        k: Number of document chunks to retrieve (default: 5).
        persist_dir: Chroma vector store persistence directory (default: ~/.oracle-rag/chroma_db).
        collection: Chroma collection name (default: "oracle_rag").
        document_id: Optional document ID to filter retrieval (from list_documents).
        page_min: Optional start of page range (inclusive). PDF only.
        page_max: Optional end of page range (inclusive). PDF only.
        tag: Optional tag to filter retrieval (from list_documents).

    Returns:
        Dictionary containing answer and sources (document_id, page).
    """
    coll = (collection or "").strip()
    if not coll or coll == "oracle_rag":
        coll = get_collection_name()
    return query_index(
        query=query,
        k=k,
        persist_dir=persist_dir or get_persist_dir(),
        collection=coll,
        document_id=document_id or None,
        page_min=page_min,
        page_max=page_max,
        tag=tag or None,
    )


@mcp.tool()
@_log_tool_errors
def add_file_tool(
    path: str,
    persist_dir: str = "",
    collection: str = "oracle_rag",
    tag: str = "",
) -> dict:
    """Add a file or directory of files to the index.

    Automatically detects format and indexes:
    - PDF (.pdf)
    - Discord export (.txt with DiscordChatExporter Guild:/Channel: header)

    Pass a file path to index one file, or a directory path to index all
    supported files in that directory (recursive).

    Args:
        path: Path to a file or directory.
        persist_dir: Chroma vector store persistence directory (default: ~/.oracle-rag/chroma_db).
        collection: Chroma collection name (default: "oracle_rag").
        tag: Optional tag for indexed documents; stored on all chunks for filtering.

    Returns:
        Dictionary containing:
        - indexed: List of successfully indexed files with format-specific stats
        - failed: List of files that failed with error messages
        - total_indexed, total_failed, persist_directory, collection_name
    """
    coll = (collection or "").strip() or get_collection_name()
    return add_file(
        path=path,
        persist_dir=persist_dir or get_persist_dir(),
        collection=coll,
        tag=tag or None,
    )


@mcp.tool()
@_log_tool_errors
def add_files_tool(
    paths: list[str],
    persist_dir: str = "",
    collection: str = "oracle_rag",
    tags: list[str] | None = None,
) -> dict:
    """Add multiple files or directories to the index in one call.

    Auto-detects format per file (PDF, Discord export). Returns both
    successful and failed entries so one bad file does not fail the batch.

    Args:
        paths: List of file or directory paths to index.
        persist_dir: Chroma vector store persistence directory (default: ~/.oracle-rag/chroma_db).
        collection: Chroma collection name (default: "oracle_rag").
        tags: Optional list of tags, one per path (same order as paths).

    Returns:
        Dictionary containing indexed entries, failed entries, and totals.
    """
    coll = (collection or "").strip() or get_collection_name()
    return add_files(
        paths=paths,
        persist_dir=persist_dir or get_persist_dir(),
        collection=coll,
        tags=tags,
    )


@mcp.tool()
@_log_tool_errors
def list_documents_tool(
    persist_dir: str = "",
    collection: str = "oracle_rag",
) -> dict:
    """List all indexed documents in the Oracle-RAG index.

    Returns unique document IDs (PDF file names, discord-alicia-1200-pcb, etc.)
    currently in the vector store, plus total chunk count.

    Args:
        persist_dir: Chroma vector store persistence directory (default: ~/.oracle-rag/chroma_db).
        collection: Chroma collection name (default: "oracle_rag").

    Returns:
        Dictionary containing documents, total_chunks, persist_directory,
        collection_name, document_details.
    """
    coll = (collection or "").strip() or get_collection_name()
    return list_documents(persist_dir=persist_dir or get_persist_dir(), collection=coll)


@mcp.tool()
@_log_tool_errors
def remove_document_tool(
    document_id: str,
    persist_dir: str = "",
    collection: str = "oracle_rag",
) -> dict:
    """Remove a document and all its chunks from the Oracle-RAG index.

    Deletes all chunks and embeddings for the given document. Use
    list_documents_tool to see document_ids (e.g. "mybook.pdf", "discord-alicia-1200-pcb").

    Args:
        document_id: Document identifier to remove (from list_documents).
        persist_dir: Chroma vector store persistence directory (default: ~/.oracle-rag/chroma_db).
        collection: Chroma collection name (default: "oracle_rag").

    Returns:
        Dictionary containing deleted_chunks, document_id, persist_directory, collection_name.
    """
    coll = (collection or "").strip() or get_collection_name()
    return remove_document(
        document_id=document_id,
        persist_dir=persist_dir or get_persist_dir(),
        collection=coll,
    )


@mcp.resource(
    "oracle-rag://documents",
    title="Indexed documents list",
    description="Read-only list of documents currently indexed in Oracle-RAG (default collection).",
)
def _documents_resource() -> str:
    """Return a plain-text list of indexed documents for the default collection."""
    try:
        result = list_documents(
            persist_dir=get_persist_dir(),
            collection=get_collection_name(),
        )
        docs = result.get("documents", [])
        total = result.get("total_chunks", 0)
        lines = [f"Indexed documents ({total} chunks total):", ""]
        for d in docs:
            lines.append(f"  - {d}")
        return "\n".join(lines) if lines else "No documents indexed."
    except Exception as e:
        return f"Error listing documents: {e}"


@mcp.prompt()
def ask_about_documents(question: str) -> str:
    """Ask a question about the indexed documents.

    Use the query_tool to search the Oracle-RAG index and return an answer
    with citations. The question will be sent as the user message to guide the AI.
    """
    return (
        f"Using the Oracle-RAG indexed documents, please answer this question: {question}\n\n"
        "Use the query_tool to retrieve relevant context before answering."
    )


def create_mcp_server() -> FastMCP:
    """Create and return the configured MCP server instance.

    Returns:
        FastMCP server instance with all tools registered.
    """
    return mcp


if __name__ == "__main__":
    # Entry point for running the server directly
    # Use stdio transport for MCP clients
    mcp.run(transport="stdio")
