"""MCP server setup using FastMCP."""

from __future__ import annotations

import logging
import os
from typing import Annotated

import anyio
from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

from pinrag import config
from pinrag.mcp.logging_utils import configure_logging, _log_tool_errors
from pinrag.mcp.tools import (
    add_files,
    list_documents,
    remove_document,
)
from pinrag.mcp.tools import (
    query as query_index,
)

logger = logging.getLogger(__name__)

mcp = FastMCP("PinRAG", json_response=True)


def _is_url(s: str) -> bool:
    """Return True if string is an HTTP(S) URL."""
    return (s or "").strip().startswith(("http://", "https://"))


def _env_set(name: str) -> bool:
    """Return True if the environment variable is set and non-empty."""
    v = os.environ.get(name)
    return v is not None and str(v).strip() != ""


def _parse_bool_env(name: str, default: bool = False) -> bool:
    """Parse a boolean env var using the same accepted values as runtime config."""
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    val = str(raw).strip().lower()
    if val in ("1", "true", "yes", "on"):
        return True
    if val in ("0", "false", "no", "off"):
        return False
    return default


def _effective_log_level_name() -> str:
    """Return normalized effective log level (DEBUG/INFO/WARNING/ERROR)."""
    level_name = (os.environ.get("PINRAG_LOG_LEVEL") or "INFO").strip().upper()
    return level_name if level_name in ("DEBUG", "INFO", "WARNING", "ERROR") else "INFO"


def _format_documents_list() -> str:
    """Sync helper: fetch and format documents list for documents_resource."""
    result = list_documents(
        persist_dir=config.get_persist_dir(),
        collection=config.get_collection_name(),
    )
    docs = result.get("documents", [])
    total = result.get("total_chunks", 0)
    details = result.get("document_details") or {}
    if not docs:
        return "No documents indexed."
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
        if info.get("file_count") is not None:
            extra.append(f"{info['file_count']} files")
        if info.get("tag"):
            extra.append(f"tag: {info['tag']}")
        suffix = f" ({', '.join(extra)})" if extra else ""
        # For YouTube with title, show title prominently with video ID
        if info.get("document_type") == "youtube" and info.get("title"):
            display_name = f"{info['title']} ({d})"
        else:
            display_name = d
        lines.append(f"  - {display_name}{suffix}")
    return "\n".join(lines)


def _format_server_config() -> str:
    """Build config string for server_config_resource.

    Runtime-only contract (OSS + Cloud):
    - If env var exists in os.environ (non-empty): explicitly set
    - Otherwise: default
    - Always show effective value from config getters.
    """
    config_items = [
        ("PINRAG_PERSIST_DIR", config.get_persist_dir),
        ("PINRAG_COLLECTION_NAME", config.get_collection_name),
        ("PINRAG_LLM_PROVIDER", config.get_llm_provider),
        ("PINRAG_LLM_MODEL", config.get_llm_model),
        ("PINRAG_EMBEDDING_PROVIDER", config.get_embedding_provider),
        ("PINRAG_EMBEDDING_MODEL", config.get_embedding_model_name),
        ("PINRAG_CHUNK_SIZE", lambda: str(config.get_chunk_size())),
        ("PINRAG_CHUNK_OVERLAP", lambda: str(config.get_chunk_overlap())),
        ("PINRAG_STRUCTURE_AWARE_CHUNKING", lambda: str(config.get_structure_aware_chunking())),
        ("PINRAG_RETRIEVE_K", lambda: str(config.get_retrieve_k())),
        ("PINRAG_USE_RERANK", lambda: str(config.get_use_rerank()).lower()),
        ("PINRAG_RERANK_RETRIEVE_K", lambda: str(config.get_rerank_retrieve_k())),
        ("PINRAG_RERANK_TOP_N", lambda: str(config.get_rerank_top_n())),
        ("PINRAG_USE_MULTI_QUERY", lambda: str(config.get_use_multi_query()).lower()),
        ("PINRAG_MULTI_QUERY_COUNT", lambda: str(config.get_multi_query_count())),
        ("PINRAG_USE_PARENT_CHILD", lambda: str(config.get_use_parent_child()).lower()),
        ("PINRAG_PARENT_CHUNK_SIZE", lambda: str(config.get_parent_chunk_size())),
        ("PINRAG_CHILD_CHUNK_SIZE", lambda: str(config.get_child_chunk_size())),
        ("PINRAG_RESPONSE_STYLE", config.get_response_style),
        ("PINRAG_GITHUB_MAX_FILE_BYTES", lambda: str(config.get_github_max_file_bytes())),
        ("PINRAG_GITHUB_DEFAULT_BRANCH", config.get_github_default_branch),
        ("PINRAG_PLAINTEXT_MAX_FILE_BYTES", lambda: str(config.get_plaintext_max_file_bytes())),
        ("PINRAG_LOG_TO_STDERR", lambda: str(_parse_bool_env("PINRAG_LOG_TO_STDERR", default=False)).lower()),
        ("PINRAG_LOG_LEVEL", _effective_log_level_name),
    ]
    set_items: list[str] = []
    default_items: list[str] = []
    for var, getter in config_items:
        val = getter()
        line = f"  {var}: {val}"
        if _env_set(var):
            set_items.append(line)
        else:
            default_items.append(line)

    lines = [
        "PinRAG MCP Server Configuration",
        "=" * 40,
        "",
        "--- Explicitly set (runtime env) ---",
        *set_items,
        "",
        "--- Defaults (not set in env) ---",
        *default_items,
        "",
        "--- API keys (status only) ---",
        f"  OPENAI_API_KEY: {'set' if _env_set('OPENAI_API_KEY') else 'not set'}",
        f"  ANTHROPIC_API_KEY: {'set' if _env_set('ANTHROPIC_API_KEY') else 'not set'}",
        f"  COHERE_API_KEY: {'set' if _env_set('COHERE_API_KEY') else 'not set'}",
        f"  GITHUB_TOKEN: {'set' if _env_set('GITHUB_TOKEN') else 'not set'}",
        f"  PINRAG_YT_PROXY_HTTP_URL: {'set' if _env_set('PINRAG_YT_PROXY_HTTP_URL') else 'not set'}",
        f"  PINRAG_YT_PROXY_HTTPS_URL: {'set' if _env_set('PINRAG_YT_PROXY_HTTPS_URL') else 'not set'}",
        "",
        "--- LangSmith observability ---",
        f"  LANGSMITH_TRACING: {os.environ.get('LANGSMITH_TRACING', 'not set')}",
        f"  LANGSMITH_ENDPOINT: {os.environ.get('LANGSMITH_ENDPOINT', 'not set')}",
        f"  LANGSMITH_PROJECT: {os.environ.get('LANGSMITH_PROJECT', 'not set')}",
        f"  LANGSMITH_API_KEY: {'set' if _env_set('LANGSMITH_API_KEY') else 'not set'}",
    ]
    return "\n".join(lines)


@mcp.tool()
@_log_tool_errors
async def query_tool(
    query: Annotated[str, Field(description="Natural language question to ask.")],
    document_id: Annotated[str, Field(description="Optional document ID to filter retrieval (from list_documents).")] = "",
    page_min: Annotated[int | None, Field(description="Optional start of page range (inclusive). PDF only.")] = None,
    page_max: Annotated[int | None, Field(description="Optional end of page range (inclusive). PDF only.")] = None,
    tag: Annotated[str, Field(description="Optional tag to filter retrieval (from list_documents).")] = "",
    document_type: Annotated[str, Field(description="Optional type to filter: 'pdf', 'youtube', 'discord', 'github', or 'plaintext'.")] = "",
    file_path: Annotated[str, Field(description="Optional file path within a document (GitHub: e.g. src/ria/api/atr.c). Use list_documents to see files.")] = "",
    response_style: Annotated[str, Field(description="Answer style: 'thorough' (detailed) or 'concise'.")] = "thorough",
    ctx: Context | None = None,
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
        document_type: Optional type to filter: "pdf", "youtube", "discord", "github", or "plaintext".
        file_path: Optional file path within a document (GitHub: e.g. src/ria/api/atr.c). Use list_documents to see files.
        response_style: Answer style: "thorough" (detailed) or "concise" (default: "thorough").

    Returns:
        Dictionary containing answer and sources (document_id, page).

    """
    style_input = (response_style or "").strip().lower()
    if style_input in ("thorough", "concise"):
        style = style_input
    else:
        style = config.get_response_style()

    def _run() -> dict:
        return query_index(
            user_query=query,
            document_id=document_id or None,
            page_min=page_min,
            page_max=page_max,
            tag=tag or None,
            document_type=document_type or None,
            file_path=file_path or None,
            response_style=style,
        )

    return await anyio.to_thread.run_sync(_run)


@mcp.tool()
@_log_tool_errors
async def add_document_tool(
    paths: Annotated[list[str], Field(description="Paths to index: file, directory, YouTube URL, or GitHub URL (e.g. https://github.com/owner/repo). Single path: [\"/path/to/file.pdf\"] or [\"https://github.com/owner/repo\"].")],
    tags: Annotated[list[str] | None, Field(description="Optional list of tags, one per path (same order as paths).")] = None,
    branch: Annotated[str | None, Field(description="For GitHub URLs: override branch (default: main). Ignored for other formats.")] = None,
    include_patterns: Annotated[list[str] | None, Field(description="For GitHub URLs: glob patterns for files to include (e.g. [\"*.md\", \"src/**/*.py\"]). Ignored for other formats.")] = None,
    exclude_patterns: Annotated[list[str] | None, Field(description="For GitHub URLs: glob patterns to exclude. Ignored for other formats.")] = None,
    ctx: Context | None = None,
) -> dict:
    """Add files, directories, YouTube videos, or GitHub repos to the index.

    Automatically detects format per path and indexes:
    - GitHub (URL, e.g. https://github.com/owner/repo or github.com/owner/repo/tree/branch)
    - YouTube (URL or video ID, e.g. https://youtu.be/xyz)
    - PDF (.pdf)
    - Discord export (.txt with DiscordChatExporter Guild:/Channel: header)

    Pass one or more paths. Single path: paths=[\"/path/to/file.pdf\"]. Uses
    server config for vector store location and collection. Returns both
    successful and failed entries so one bad path does not fail the batch.

    Args:
        paths: List of file paths, directory paths, YouTube URLs, or GitHub URLs to index.
        tags: Optional list of tags, one per path (same order as paths).
        branch: For GitHub URLs: override branch (default: main). Ignored for other formats.
        include_patterns: For GitHub URLs: glob patterns for files to include (e.g. ["*.md", "src/**/*.py"]).
        exclude_patterns: For GitHub URLs: glob patterns to exclude. Ignored for other formats.

    Returns:
        Dictionary containing indexed entries, failed entries, and totals.

    """

    def _run() -> dict:
        return add_files(
            paths=paths,
            persist_dir=config.get_persist_dir(),
            collection=config.get_collection_name(),
            tags=tags,
            branch=branch,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )

    return await anyio.to_thread.run_sync(_run)


@mcp.tool()
@_log_tool_errors
async def add_url_tool(
    paths: Annotated[
        list[str],
        Field(description="URLs to index: YouTube video/playlist or GitHub repo."),
    ],
    tags: Annotated[
        list[str] | None, Field(description="Optional list of tags, one per URL.")
    ] = None,
    branch: Annotated[str | None, Field(description="For GitHub: override branch (default: main).")] = None,
    include_patterns: Annotated[
        list[str] | None, Field(description="For GitHub: glob patterns for files to include.")
    ] = None,
    exclude_patterns: Annotated[
        list[str] | None, Field(description="For GitHub: glob patterns to exclude.")
    ] = None,
    ctx: Context | None = None,
) -> dict:
    """Add YouTube videos/playlists or GitHub repos to the index via URL.

    For local files or directories, use add_document_tool instead.
    """
    input_paths = list(paths or [])
    if not input_paths:
        raise ValueError("paths cannot be empty")
    for i, p in enumerate(input_paths):
        if not _is_url(p):
            raise ValueError(
                f"path[{i}] is not a URL. Use add_document_tool for local files or directories."
            )
    if tags is not None and len(tags) != len(input_paths):
        raise ValueError("tags must have same length as paths when provided")

    def _run() -> dict:
        return add_files(
            paths=input_paths,
            persist_dir=config.get_persist_dir(),
            collection=config.get_collection_name(),
            tags=tags,
            branch=branch,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )

    return await anyio.to_thread.run_sync(_run)


@mcp.tool()
@_log_tool_errors
async def list_documents_tool(
    tag: Annotated[str, Field(description="Optional tag to filter: only list documents that have this tag.")] = "",
    ctx: Context | None = None,
) -> dict:
    """List all indexed documents in the PinRAG index.

    Returns unique document IDs (PDF file names, video IDs, discord-alicia-1200-pcb, owner/repo/path for GitHub, etc.)
    currently in the vector store, plus total chunk count. Uses server config
    for vector store location and collection.

    Args:
        tag: Optional tag to filter: only list documents that have this tag.

    Returns:
        Dictionary containing documents, total_chunks, persist_directory,
        collection_name, document_details.

    """

    def _run() -> dict:
        return list_documents(
            persist_dir=config.get_persist_dir(),
            collection=config.get_collection_name(),
            tag=tag or None,
        )

    return await anyio.to_thread.run_sync(_run)


@mcp.tool()
@_log_tool_errors
async def remove_document_tool(
    document_id: Annotated[str, Field(description="Document identifier to remove (from list_documents_tool).")],
    ctx: Context | None = None,
) -> dict:
    """Remove a document and all its chunks from the PinRAG index.

    Deletes all chunks and embeddings for the given document. Use
    list_documents_tool to see document_ids (e.g. "mybook.pdf", "bwgLXEQdq20", "discord-alicia-1200-pcb", "owner/repo/path" for GitHub).
    Uses server config for vector store location and collection.

    Args:
        document_id: Document identifier to remove (from list_documents_tool).

    Returns:
        Dictionary containing deleted_chunks, document_id, persist_directory, collection_name.

    """

    def _run() -> dict:
        return remove_document(
            document_id=document_id,
            persist_dir=config.get_persist_dir(),
            collection=config.get_collection_name(),
        )

    return await anyio.to_thread.run_sync(_run)


@mcp.resource(
    "pinrag://documents",
    title="Indexed documents list",
    description="Read-only list of documents currently indexed in PinRAG (default collection).",
)
async def documents_resource() -> str:
    """Return a plain-text list of indexed documents for the default collection.

    For PDFs: shows page count. For Discord: shows size (messages or bytes).
    For YouTube: shows video title when available, with video ID in parentheses.
    Shows tag when attached to a document.
    """
    logger.debug("Resource pinrag://documents read")
    try:
        return await anyio.to_thread.run_sync(_format_documents_list)
    except Exception as e:
        logger.exception("Resource pinrag://documents failed")
        return f"Error listing documents: {e}"


@mcp.resource(
    "pinrag://server-config",
    title="Server configuration",
    description="Environment variables and config params used by the PinRAG MCP server.",
)
async def server_config_resource() -> str:
    """Return plain-text summary: env vars that are set (top), defaults (bottom)."""
    logger.debug("Resource pinrag://server-config read")
    return await anyio.to_thread.run_sync(_format_server_config)


@mcp.prompt()
def use_pinrag(request: str = "") -> str:
    """Use PinRAG to query, index, list, or remove documents.

    Routes to the correct tool based on the request:
    - Query / question  → query_tool
    - Index / add       → add_url_tool (URLs) or add_document_tool (files/dirs)
    - List / show       → list_documents_tool
    - Remove / delete   → remove_document_tool
    """
    return (
        f"Use PinRAG to fulfil this request: {request or 'not specified'}.\n\n"
        "Available tools and when to use them:\n\n"
        "query_tool — answer a question from indexed documents.\n"
        "  Required: query (str). "
        "  Optional: document_id (filter to one doc, from list_documents_tool), "
        "page_min/page_max (PDF page range), tag (filter by tag), "
        "document_type ('pdf', 'youtube', 'discord', 'github', 'plaintext'), "
        "file_path (filter to a file within a doc, e.g. src/foo.c for GitHub), "
        "response_style ('thorough' or 'concise').\n\n"
        "add_url_tool — index YouTube videos/playlists or GitHub repos via URL only.\n"
        "  Required: paths (list of URLs). "
        "  Optional: tags (list, one per URL), branch (GitHub only), "
        "include_patterns / exclude_patterns (GitHub only).\n\n"
        "add_document_tool — index local files, directories, or URLs (all-in-one).\n"
        "  Required: paths (list of str: file paths, dir paths, YouTube URLs, GitHub URLs). "
        "  Optional: tags (list, one per path), branch (GitHub only), "
        "include_patterns / exclude_patterns (GitHub only).\n\n"
        "list_documents_tool — list all indexed documents and chunk counts.\n"
        "  Optional: tag (filter by tag).\n\n"
        "remove_document_tool — remove a document and all its chunks.\n"
        "  Required: document_id (get exact ID from list_documents_tool first).\n\n"
        "If the request is ambiguous, call list_documents_tool first to show what is indexed, "
        "then decide which tool to use."
    )

