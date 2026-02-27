"""MCP server setup using FastMCP."""

from __future__ import annotations

import functools
import logging
import os
import sys

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from oracle_rag.config import get_persist_dir
from oracle_rag.mcp.tools import add_pdf, add_pdfs, list_pdfs, query_pdf, remove_pdf

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
def query_pdf_tool(
    query: str,
    k: int = 5,
    persist_dir: str = "",
    collection: str = "oracle_rag",
    document_id: str = "",
    page_min: int | None = None,
    page_max: int | None = None,
    tag: str = "",
) -> dict:
    """Query indexed PDFs and return an answer with citations.

    This tool searches through all indexed PDF documents and uses RAG
    (Retrieval-Augmented Generation) to provide an answer based on the
    retrieved context, along with source citations.

    Args:
        query: Natural language question to ask about the indexed PDFs.
        k: Number of document chunks to retrieve (default: 5).
        persist_dir: Chroma vector store persistence directory (default: ~/.oracle-rag/chroma_db).
        collection: Chroma collection name (default: "oracle_rag").
        document_id: Optional document ID to filter retrieval (e.g. PDF file name from list_pdfs).
        page_min: Optional start of page range (inclusive). Use with page_max.
        page_max: Optional end of page range (inclusive). Single page: page_min=64, page_max=64.
        tag: Optional tag to filter retrieval (e.g. "PI_PICO" from list_pdfs document_details).

    Returns:
        Dictionary containing:
        - answer: The generated answer text
        - sources: List of source citations with document_id and page number
    """
    return query_pdf(
        query=query,
        k=k,
        persist_dir=persist_dir or get_persist_dir(),
        collection=collection,
        document_id=document_id or None,
        page_min=page_min,
        page_max=page_max,
        tag=tag or None,
    )


@mcp.tool()
@_log_tool_errors
def add_pdf_tool(
    pdf_path: str,
    persist_dir: str = "",
    collection: str = "oracle_rag",
    tag: str = "",
) -> dict:
    """Add a PDF document to the index.

    This tool processes a PDF file, extracts text, chunks it, generates
    embeddings, and stores it in the vector database for later querying.

    Args:
        pdf_path: Path to the PDF file to index.
        persist_dir: Chroma vector store persistence directory (default: ~/.oracle-rag/chroma_db).
        collection: Chroma collection name (default: "oracle_rag").
        tag: Optional single tag for this document (e.g. "amiga"); stored on all chunks for filtering.

    Returns:
        Dictionary containing indexing results:
        - source_path: Path to the indexed PDF
        - total_pages: Number of pages processed
        - total_chunks: Number of text chunks created
        - persist_directory: Where the index is stored
        - collection_name: Collection name used
    """
    return add_pdf(
        pdf_path=pdf_path,
        persist_dir=persist_dir or get_persist_dir(),
        collection=collection,
        tag=tag or None,
    )


@mcp.tool()
@_log_tool_errors
def add_pdfs_tool(
    pdf_paths: list[str],
    persist_dir: str = "",
    collection: str = "oracle_rag",
    tags: list[str] | None = None,
) -> dict:
    """Add multiple PDF documents to the index in one call.

    This tool indexes each PDF independently and returns both successful and failed
    files so one bad file does not fail the whole batch.

    Args:
        pdf_paths: List of PDF paths to index.
        persist_dir: Chroma vector store persistence directory (default: ~/.oracle-rag/chroma_db).
        collection: Chroma collection name (default: "oracle_rag").
        tags: Optional list of tags, one per PDF (same order as pdf_paths). Empty string = no tag.

    Returns:
        Dictionary containing indexed entries, failed entries, and totals.
    """
    return add_pdfs(
        pdf_paths=pdf_paths,
        persist_dir=persist_dir or get_persist_dir(),
        collection=collection,
        tags=tags,
    )


@mcp.tool()
@_log_tool_errors
def list_pdfs_tool(
    persist_dir: str = "",
    collection: str = "oracle_rag",
) -> dict:
    """List all indexed PDFs (books) in the Oracle-RAG index.

    Returns the unique document names (e.g. PDF file names) currently in the
    vector store, plus total chunk count. Use this to see which books are
    available for querying.

    Args:
        persist_dir: Chroma vector store persistence directory (default: ~/.oracle-rag/chroma_db).
        collection: Chroma collection name (default: "oracle_rag").

    Returns:
        Dictionary containing:
        - documents: List of unique document identifiers (typically file names)
        - total_chunks: Total number of chunks in the index
        - persist_directory: Path to the Chroma store
        - collection_name: Collection name used
        - document_details: Per-document stats (upload_timestamp, pages, bytes, chunks, tag) when available
    """
    return list_pdfs(persist_dir=persist_dir or get_persist_dir(), collection=collection)


@mcp.tool()
@_log_tool_errors
def remove_pdf_tool(
    document_id: str,
    persist_dir: str = "",
    collection: str = "oracle_rag",
) -> dict:
    """Remove a PDF and all its chunks and embeddings from the Oracle-RAG index.

    Deletes all chunks and their embeddings for the given document from the
    Chroma vector store. Use list_pdfs_tool to see the exact document_id
    (typically the PDF file name) to remove.

    Args:
        document_id: Document identifier to remove (same as in list_pdfs, e.g. "mybook.pdf").
        persist_dir: Chroma vector store persistence directory (default: ~/.oracle-rag/chroma_db).
        collection: Chroma collection name (default: "oracle_rag").

    Returns:
        Dictionary containing:
        - deleted_chunks: Number of chunks (and embeddings) removed
        - document_id: The document that was removed
        - persist_directory: Path to the Chroma store
        - collection_name: Collection name used
    """
    return remove_pdf(
        document_id=document_id,
        persist_dir=persist_dir or get_persist_dir(),
        collection=collection,
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
