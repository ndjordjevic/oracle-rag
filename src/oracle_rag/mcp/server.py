"""MCP server setup using FastMCP."""

from __future__ import annotations

import functools
import inspect
import logging
import os
import sys
from typing import Annotated

from dotenv import load_dotenv
from pydantic import Field
from mcp.server.fastmcp import FastMCP

from oracle_rag.config import (
    get_chunk_overlap,
    get_chunk_size,
    get_child_chunk_size,
    get_collection_name,
    get_embedding_model_name,
    get_embedding_provider,
    get_llm_model,
    get_llm_provider,
    get_multi_query_count,
    get_parent_chunk_size,
    get_persist_dir,
    get_retrieve_k,
    get_response_style,
    get_rerank_retrieve_k,
    get_rerank_top_n,
    get_structure_aware_chunking,
    get_use_multi_query,
    get_use_parent_child,
    get_use_rerank,
)
from oracle_rag.mcp.tools import (
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


def _user_friendly_api_error(exc: BaseException) -> str | None:
    """Return a short, user-friendly message for API key / auth errors, or None."""
    msg = str(exc).lower()
    if "api key" in msg or "api_key" in msg or "authentication" in msg or "invalid key" in msg or "no api key" in msg:
        if "anthropic" in msg or "claude" in msg:
            return "Anthropic API key missing or invalid. Set ANTHROPIC_API_KEY in ~/.oracle-rag/.env (or your config)."
        if "cohere" in msg:
            return "Cohere API key missing or invalid. Set COHERE_API_KEY in ~/.oracle-rag/.env (or your config)."
        return "OpenAI API key not found or invalid. Set OPENAI_API_KEY in ~/.oracle-rag/.env (or your config)."
    if "rate" in msg and "limit" in msg:
        return "API rate limit exceeded. Please try again in a moment."
    return None


def _log_tool_errors(fn):
    """Decorator: log exceptions to stderr (Cursor Output) then re-raise so client gets the error.
    Preserves the wrapped function's signature so MCP/FastMCP schema introspection sees all parameters.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            _log.exception("Tool %s failed", fn.__name__)
            friendly = _user_friendly_api_error(e)
            if friendly:
                raise RuntimeError(friendly) from e
            raise

    wrapper.__signature__ = inspect.signature(fn)
    wrapper.__annotations__ = fn.__annotations__
    return wrapper


@mcp.tool()
@_log_tool_errors
def query_tool(
    query: Annotated[str, Field(description="Natural language question to ask.")],
    document_id: Annotated[str, Field(description="Optional document ID to filter retrieval (from list_documents).")] = "",
    page_min: Annotated[int | None, Field(description="Optional start of page range (inclusive). PDF only.")] = None,
    page_max: Annotated[int | None, Field(description="Optional end of page range (inclusive). PDF only.")] = None,
    tag: Annotated[str, Field(description="Optional tag to filter retrieval (from list_documents).")] = "",
    document_type: Annotated[str, Field(description="Optional type to filter: 'pdf', 'youtube', or 'discord'.")] = "",
    response_style: Annotated[str, Field(description="Answer style: 'thorough' (detailed) or 'concise'.")] = "thorough",
) -> dict:
    """Query indexed documents and return an answer with citations.

    Searches through all indexed documents (PDF, Discord, etc.) and uses RAG
    to provide an answer based on retrieved context, with source citations.

    Args:
        query: Natural language question to ask.
        document_id: Optional document ID to filter retrieval (from list_documents).
        page_min: Optional start of page range (inclusive). PDF only.
        page_max: Optional end of page range (inclusive). PDF only.
        tag: Optional tag to filter retrieval (from list_documents).
        document_type: Optional type to filter: "pdf", "youtube", or "discord".
        response_style: Answer style: "thorough" (detailed) or "concise" (default: "thorough").

    Returns:
        Dictionary containing answer and sources (document_id, page).
    """
    style = "concise" if (response_style or "").strip().lower() == "concise" else "thorough"
    return query_index(
        query=query,
        document_id=document_id or None,
        page_min=page_min,
        page_max=page_max,
        tag=tag or None,
        document_type=document_type or None,
        response_style=style,
    )


@mcp.tool()
@_log_tool_errors
def add_document_tool(
    paths: Annotated[list[str], Field(description="Paths to index: file, directory, or YouTube URL (e.g. https://youtu.be/ID). Single path: [\"/path/to/file.pdf\"].")],
    tags: Annotated[list[str] | None, Field(description="Optional list of tags, one per path (same order as paths).")] = None,
) -> dict:
    """Add files, directories, or YouTube videos to the index.

    Automatically detects format per path and indexes:
    - YouTube (URL or video ID, e.g. https://youtu.be/xyz)
    - PDF (.pdf)
    - Discord export (.txt with DiscordChatExporter Guild:/Channel: header)

    Pass one or more paths. Single path: paths=[\"/path/to/file.pdf\"]. Uses
    server config for vector store location and collection. Returns both
    successful and failed entries so one bad path does not fail the batch.

    Args:
        paths: List of file paths, directory paths, or YouTube URLs to index.
        tags: Optional list of tags, one per path (same order as paths).

    Returns:
        Dictionary containing indexed entries, failed entries, and totals.
    """
    return add_files(
        paths=paths,
        persist_dir=get_persist_dir(),
        collection=get_collection_name(),
        tags=tags,
    )


@mcp.tool()
@_log_tool_errors
def list_documents_tool(
    tag: Annotated[str, Field(description="Optional tag to filter: only list documents that have this tag.")] = "",
) -> dict:
    """List all indexed documents in the Oracle-RAG index.

    Returns unique document IDs (PDF file names, video IDs, discord-alicia-1200-pcb, etc.)
    currently in the vector store, plus total chunk count. Uses server config
    for vector store location and collection.

    Args:
        tag: Optional tag to filter: only list documents that have this tag.

    Returns:
        Dictionary containing documents, total_chunks, persist_directory,
        collection_name, document_details.
    """
    return list_documents(
        persist_dir=get_persist_dir(),
        collection=get_collection_name(),
        tag=tag or None,
    )


@mcp.tool()
@_log_tool_errors
def remove_document_tool(
    document_id: Annotated[str, Field(description="Document identifier to remove (from list_documents_tool).")],
) -> dict:
    """Remove a document and all its chunks from the Oracle-RAG index.

    Deletes all chunks and embeddings for the given document. Use
    list_documents_tool to see document_ids (e.g. "mybook.pdf", "bwgLXEQdq20", "discord-alicia-1200-pcb").
    Uses server config for vector store location and collection.

    Args:
        document_id: Document identifier to remove (from list_documents_tool).

    Returns:
        Dictionary containing deleted_chunks, document_id, persist_directory, collection_name.
    """
    return remove_document(
        document_id=document_id,
        persist_dir=get_persist_dir(),
        collection=get_collection_name(),
    )


@mcp.resource(
    "oracle-rag://documents",
    title="Indexed documents list",
    description="Read-only list of documents currently indexed in Oracle-RAG (default collection).",
)
def documents_resource() -> str:
    """Return a plain-text list of indexed documents for the default collection.

    For PDFs: shows page count. For Discord: shows size (messages or bytes).
    For YouTube: shows video title when available, with video ID in parentheses.
    Shows tag when attached to a document.
    """
    try:
        result = list_documents(
            persist_dir=get_persist_dir(),
            collection=get_collection_name(),
        )
        docs = result.get("documents", [])
        total = result.get("total_chunks", 0)
        details = result.get("document_details") or {}
        lines = [f"Indexed documents ({total} chunks total):", ""]
        for d in docs:
            info = details.get(d, {})
            extra: list[str] = []
            if info.get("pages") is not None:
                extra.append(f"{info['pages']} pages")
            if info.get("messages") is not None:
                extra.append(f"{info['messages']} messages")
            if info.get("segments") is not None:
                extra.append(f"{info['segments']} segments")
            if info.get("bytes") is not None and "messages" not in info:
                b = info["bytes"]
                size = f"{b / 1024:.1f} KB" if b >= 1024 else f"{b} B"
                extra.append(size)
            if info.get("tag"):
                extra.append(f"tag: {info['tag']}")
            suffix = f" ({', '.join(extra)})" if extra else ""
            # For YouTube with title, show title prominently with video ID
            if info.get("document_type") == "youtube" and info.get("title"):
                display_name = f"{info['title']} ({d})"
            else:
                display_name = d
            lines.append(f"  - {display_name}{suffix}")
        return "\n".join(lines) if lines else "No documents indexed."
    except Exception as e:
        return f"Error listing documents: {e}"


def _env_set(name: str) -> bool:
    v = os.environ.get(name)
    return v is not None and str(v).strip() != ""


@mcp.resource(
    "oracle-rag://server-config",
    title="Server configuration",
    description="Environment variables and config params used by the Oracle-RAG MCP server.",
)
def server_config_resource() -> str:
    """Return plain-text summary: env vars that are set (top), defaults (bottom)."""
    config_items = [
        ("ORACLE_RAG_PERSIST_DIR", get_persist_dir),
        ("ORACLE_RAG_COLLECTION_NAME", get_collection_name),
        ("ORACLE_RAG_LLM_PROVIDER", get_llm_provider),
        ("ORACLE_RAG_LLM_MODEL", get_llm_model),
        ("ORACLE_RAG_EMBEDDING_PROVIDER", get_embedding_provider),
        ("ORACLE_RAG_EMBEDDING_MODEL", get_embedding_model_name),
        ("ORACLE_RAG_CHUNK_SIZE", lambda: str(get_chunk_size())),
        ("ORACLE_RAG_CHUNK_OVERLAP", lambda: str(get_chunk_overlap())),
        ("ORACLE_RAG_STRUCTURE_AWARE_CHUNKING", lambda: str(get_structure_aware_chunking())),
        ("ORACLE_RAG_RETRIEVE_K", lambda: str(get_retrieve_k())),
        ("ORACLE_RAG_USE_RERANK", lambda: str(get_use_rerank()).lower()),
        ("ORACLE_RAG_RERANK_RETRIEVE_K", lambda: str(get_rerank_retrieve_k())),
        ("ORACLE_RAG_RERANK_TOP_N", lambda: str(get_rerank_top_n())),
        ("ORACLE_RAG_USE_MULTI_QUERY", lambda: str(get_use_multi_query()).lower()),
        ("ORACLE_RAG_MULTI_QUERY_COUNT", lambda: str(get_multi_query_count())),
        ("ORACLE_RAG_USE_PARENT_CHILD", lambda: str(get_use_parent_child()).lower()),
        ("ORACLE_RAG_PARENT_CHUNK_SIZE", lambda: str(get_parent_chunk_size())),
        ("ORACLE_RAG_CHILD_CHUNK_SIZE", lambda: str(get_child_chunk_size())),
        ("ORACLE_RAG_RESPONSE_STYLE", get_response_style),
    ]
    set_items: list[str] = []
    default_items: list[str] = []
    for var, getter in config_items:
        val = getter()
        line = f"  {var}: {val}"
        if _env_set(var):
            set_items.append(line)
        else:
            default_items.append(line + " (default)")

    lines = [
        "Oracle-RAG MCP Server Configuration",
        "=" * 40,
        "",
        "--- Set (from env) ---",
        *set_items,
        "",
        "--- Defaults (not set) ---",
        *default_items,
        "",
        "--- API keys (sensitive; only status) ---",
        f"  OPENAI_API_KEY: {'set' if os.environ.get('OPENAI_API_KEY') else 'not set'}",
        f"  ANTHROPIC_API_KEY: {'set' if os.environ.get('ANTHROPIC_API_KEY') else 'not set'}",
        f"  COHERE_API_KEY: {'set' if os.environ.get('COHERE_API_KEY') else 'not set'}",
    ]
    return "\n".join(lines)


@mcp.prompt()
def ask_about_documents(question: str) -> str:
    """Ask a question about the indexed documents.

    Use the query_tool to search the Oracle-RAG index and return an answer
    with citations. The question will be sent as the user message to guide the AI.
    """
    return (
        f"Answer this question using the Oracle-RAG indexed documents: {question}\n\n"
        f"You MUST call the query_tool first to retrieve relevant context. "
        "Required: query (the question). Optional params: document_id (filter to one doc), "
        "page_min/page_max (PDF page range only), tag (filter by tag), document_type ('pdf', 'youtube', 'discord'), response_style ('thorough' or 'concise'). "
        "Sources may show 'page' (PDF) or 'start' (YouTube timestamp in seconds). "
        "Use list_documents_tool to see available docs and tags. "
        "Then use the returned answer and sources in your response. Do not answer from memory alone."
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
