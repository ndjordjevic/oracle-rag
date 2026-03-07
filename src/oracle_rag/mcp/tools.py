"""MCP tool implementations that wrap Oracle-RAG functionality."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from langsmith import traceable

from oracle_rag.embeddings import get_embedding_model
from oracle_rag.indexing import (
    DiscordIndexResult,
    IndexResult,
    index_discord,
    index_pdf,
)
from oracle_rag.llm import get_chat_model
from oracle_rag.rag import run_rag
from oracle_rag.config import get_collection_name, get_persist_dir
from oracle_rag.vectorstore import get_chroma_store


def _detect_file_format(path: Path) -> Literal["pdf", "discord"] | None:
    """Detect supported format: PDF or DiscordChatExporter TXT.

    Returns "pdf", "discord", or None if unsupported.
    """
    if not path.is_file():
        return None
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix == ".txt":
        # DiscordChatExporter has header with Guild: and Channel:
        try:
            head = path.read_text(encoding="utf-8", errors="replace")[:2048]
            lines = head.split("\n")[:30]
            has_guild = any(line.strip().startswith("Guild:") for line in lines)
            has_channel = any(line.strip().startswith("Channel:") for line in lines)
            if has_guild and has_channel:
                return "discord"
        except OSError:
            pass
        return None
    return None


@traceable(name="query", run_type="tool")
def query(
    query: str,
    k: int = 5,
    persist_dir: str = "",
    collection: str | None = None,
    document_id: str | None = None,
    page_min: int | None = None,
    page_max: int | None = None,
    tag: str | None = None,
) -> dict[str, Any]:
    """Query indexed documents (PDF, Discord) and return an answer with citations.

    Args:
        query: Natural language question to ask.
        k: Number of chunks to retrieve (default: 5).
        persist_dir: Chroma persistence directory (default: "chroma_db").
        collection: Chroma collection name (default: "oracle_rag").
        document_id: Optional document ID to filter retrieval (e.g. from list_documents).
        page_min: Optional start of page range (inclusive). Use with page_max. PDF only.
        page_max: Optional end of page range (inclusive). Single page: page_min=64, page_max=64. PDF only.
        tag: Optional tag to filter retrieval (e.g. from list_documents document_details).

    Returns:
        Dictionary with "answer" (str) and "sources" (list of dicts with document_id and page).

    Raises:
        ValueError: If query is empty or invalid.
        FileNotFoundError: If persist_dir doesn't exist.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    if not isinstance(k, int) or k < 1 or k > 100:
        raise ValueError("k must be an integer between 1 and 100")
    if collection is None or not str(collection).strip():
        collection = get_collection_name()
    else:
        collection = str(collection).strip()
    if (page_min is not None) != (page_max is not None):
        raise ValueError("page_min and page_max must be provided together for page range filter")
    if page_min is not None and page_max is not None and page_min > page_max:
        raise ValueError("page_min must be <= page_max")

    _persist = (persist_dir or "").strip() or get_persist_dir()
    persist_path = Path(_persist).expanduser().resolve()
    if not persist_path.exists():
        raise FileNotFoundError(
            f"Persistence directory does not exist: {_persist}. "
            "Index some documents first using add_file."
        )

    embedding = get_embedding_model()
    llm = get_chat_model()

    doc_id_filter = document_id.strip() if document_id and str(document_id).strip() else None
    tag_filter = tag.strip() if tag and str(tag).strip() else None
    rag_result = run_rag(
        query,
        llm,
        k=k,
        persist_directory=str(persist_path),
        collection_name=collection,
        embedding=embedding,
        document_id=doc_id_filter,
        page_min=page_min,
        page_max=page_max,
        tag=tag_filter,
    )

    return {
        "answer": rag_result.answer,
        "sources": [
            {
                "document_id": str(s.get("document_id", "unknown")),
                "page": int(s.get("page", 0)),
            }
            for s in rag_result.sources
        ],
    }


@traceable(name="add_file", run_type="tool")
def add_file(
    path: str,
    persist_dir: str = "",
    collection: str | None = None,
    tag: str | None = None,
) -> dict[str, Any]:
    """Add a file or directory of files to the index.

    Automatically detects format: PDF (.pdf) or Discord export (.txt with
    DiscordChatExporter header). Indexes the file or all supported files
    in the directory.

    Args:
        path: Path to a single file or directory containing .pdf / .txt files.
        persist_dir: Chroma persistence directory (default: "chroma_db").
        collection: Chroma collection name (default: "oracle_rag").
        tag: Optional tag for indexed documents; stored on all chunks for filtering.

    Returns:
        Dictionary with "indexed" (list of per-file results), "failed" (list of
        errors), "total_indexed", "total_failed", "persist_directory", "collection_name".
    """
    if not path or not str(path).strip():
        raise ValueError("path cannot be empty")
    if collection is None or not str(collection).strip():
        collection = get_collection_name()
    else:
        collection = str(collection).strip()

    _persist = (persist_dir or "").strip() or get_persist_dir()
    base = Path(path).expanduser().resolve()
    if not base.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    files_to_index: list[Path] = []
    if base.is_file():
        fmt = _detect_file_format(base)
        if fmt:
            files_to_index.append(base)
        else:
            raise ValueError(
                f"Unsupported file format: {base.name}. "
                "Supported: .pdf, .txt (DiscordChatExporter with Guild:/Channel: header)."
            )
    else:
        for p in sorted(base.rglob("*")):
            if p.is_file() and _detect_file_format(p):
                files_to_index.append(p)

    if not files_to_index:
        return {
            "indexed": [],
            "failed": [],
            "total_indexed": 0,
            "total_failed": 0,
            "persist_directory": str(Path(_persist).expanduser().resolve()),
            "collection_name": collection,
        }

    embedding = get_embedding_model()
    tag_clean = tag.strip() if tag and str(tag).strip() else None
    indexed: list[dict[str, Any]] = []
    failed: list[dict[str, str]] = []

    for f in files_to_index:
        try:
            fmt = _detect_file_format(f)
            if fmt == "pdf":
                result: IndexResult = index_pdf(
                    f,
                    persist_directory=_persist,
                    collection_name=collection,
                    embedding=embedding,
                    tag=tag_clean,
                )
                indexed.append({
                    "path": str(f),
                    "format": "pdf",
                    "source_path": str(result.source_path),
                    "total_pages": result.total_pages,
                    "total_chunks": result.total_chunks,
                })
            elif fmt == "discord":
                result_d: DiscordIndexResult = index_discord(
                    f,
                    persist_directory=_persist,
                    collection_name=collection,
                    embedding=embedding,
                    tag=tag_clean,
                )
                indexed.append({
                    "path": str(f),
                    "format": "discord",
                    "source_path": str(result_d.source_path),
                    "document_id": result_d.document_id,
                    "channel": result_d.channel,
                    "guild": result_d.guild,
                    "total_messages": result_d.total_messages,
                    "total_chunks": result_d.total_chunks,
                })
            else:
                failed.append({"path": str(f), "error": "Unsupported format"})
        except Exception as e:
            failed.append({"path": str(f), "error": str(e)})

    return {
        "indexed": indexed,
        "failed": failed,
        "total_indexed": len(indexed),
        "total_failed": len(failed),
        "persist_directory": str(Path(_persist).expanduser().resolve()),
        "collection_name": collection,
    }


@traceable(name="add_files", run_type="tool")
def add_files(
    paths: list[str],
    persist_dir: str = "",
    collection: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Add multiple files or directories to the index in one call.

    Automatically detects format per file (PDF, Discord export). Continues
    indexing even if some paths fail.

    Args:
        paths: List of file or directory paths to index.
        persist_dir: Chroma persistence directory (default: "chroma_db").
        collection: Chroma collection name (default: "oracle_rag").
        tags: Optional list of tags, one per path (same order as paths). Empty string = no tag.

    Returns:
        Dictionary containing indexed file results, failed file errors, and totals.
    """
    if not paths:
        raise ValueError("paths cannot be empty")
    if collection is None or not str(collection).strip():
        collection = get_collection_name()
    else:
        collection = str(collection).strip()
    if tags is not None and len(tags) != len(paths):
        raise ValueError("tags must have same length as paths when provided")

    all_indexed: list[dict[str, Any]] = []
    all_failed: list[dict[str, str]] = []

    for i, raw_path in enumerate(paths):
        if not raw_path or not str(raw_path).strip():
            all_failed.append({"path": str(raw_path), "error": "path cannot be empty"})
            continue
        doc_tag: str | None = None
        if tags is not None and i < len(tags) and tags[i] and str(tags[i]).strip():
            doc_tag = str(tags[i]).strip()
        try:
            r = add_file(
                path=raw_path,
                persist_dir=_persist,
                collection=collection,
                tag=doc_tag,
            )
            all_indexed.extend(r["indexed"])
            all_failed.extend(r["failed"])
        except Exception as e:
            all_failed.append({"path": str(raw_path), "error": str(e)})

    return {
        "indexed": all_indexed,
        "failed": all_failed,
        "total_indexed": len(all_indexed),
        "total_failed": len(all_failed),
        "persist_directory": str(Path(_persist).expanduser().resolve()),
        "collection_name": collection,
    }


@traceable(name="list_documents", run_type="tool")
def list_documents(
    persist_dir: str | None = None,
    collection: str | None = None,
) -> dict[str, Any]:
    """List all indexed documents (PDF, Discord, etc.) in the Oracle-RAG index.

    Args:
        persist_dir: Chroma persistence directory (default: from ORACLE_RAG_PERSIST_DIR or chroma_db).
        collection: Chroma collection name (default: "oracle_rag").

    Returns:
        Dictionary with "documents" (list of unique document IDs)
        and "total_chunks" (total number of chunks in the index).
    """
    if collection is None or not str(collection).strip():
        collection = get_collection_name()
    else:
        collection = str(collection).strip()

    _persist = (persist_dir or "").strip() or get_persist_dir()
    persist_path = Path(_persist).expanduser().resolve()
    if not persist_path.exists():
        return {
            "documents": [],
            "total_chunks": 0,
            "persist_directory": str(persist_path),
            "collection_name": collection,
            "document_details": {},
        }

    store = get_chroma_store(
        persist_directory=_persist,
        collection_name=collection,
    )
    data = store.get(include=["metadatas"])
    metadatas = data.get("metadatas") or []

    doc_ids: set[str] = set()
    document_details: dict[str, dict[str, Any]] = {}
    for meta in metadatas:
        if not isinstance(meta, dict):
            continue
        doc_id = str(
            meta.get("document_id")
            or meta.get("file_name")
            or meta.get("source")
            or "unknown"
        )
        doc_ids.add(doc_id)
        if doc_id not in document_details:
            details: dict[str, Any] = {}
            if meta.get("upload_timestamp") is not None:
                details["upload_timestamp"] = meta["upload_timestamp"]
            if meta.get("doc_pages") is not None:
                details["pages"] = meta["doc_pages"]
            if meta.get("doc_messages") is not None:
                details["messages"] = meta["doc_messages"]
            if meta.get("doc_bytes") is not None:
                details["bytes"] = meta["doc_bytes"]
            if meta.get("doc_total_chunks") is not None:
                details["chunks"] = meta["doc_total_chunks"]
            if meta.get("tag") is not None and str(meta.get("tag", "")).strip():
                details["tag"] = str(meta["tag"]).strip()
            if details:
                document_details[doc_id] = details

    return {
        "documents": sorted(doc_ids),
        "total_chunks": len(metadatas),
        "persist_directory": str(persist_path),
        "collection_name": collection,
        "document_details": {k: document_details[k] for k in sorted(document_details)},
    }


@traceable(name="remove_document", run_type="tool")
def remove_document(
    document_id: str,
    persist_dir: str = "",
    collection: str | None = None,
) -> dict[str, Any]:
    """Remove a document and all its chunks and embeddings from the Chroma index.

    The document_id must match exactly the name shown in list_documents (e.g.
    "mybook.pdf" or "discord-alicia-1200-pcb"). All chunks and their embeddings
    for that document are deleted from the vector store.

    Args:
        document_id: Document identifier to remove (same as in list_documents).
        persist_dir: Chroma persistence directory (default: "chroma_db").
        collection: Chroma collection name (default: "oracle_rag").

    Returns:
        Dictionary with "deleted_chunks" (int), "document_id" (str),
        "persist_directory", "collection_name".

    Raises:
        ValueError: If document_id is empty or collection is empty.
        FileNotFoundError: If persist_dir does not exist.
    """
    if not document_id or not str(document_id).strip():
        raise ValueError("document_id cannot be empty")
    if collection is None or not str(collection).strip():
        collection = get_collection_name()
    else:
        collection = str(collection).strip()

    _persist = (persist_dir or "").strip() or get_persist_dir()
    persist_path = Path(_persist).expanduser().resolve()
    if not persist_path.exists():
        raise FileNotFoundError(
            f"Persistence directory does not exist: {_persist}"
        )

    store = get_chroma_store(
        persist_directory=_persist,
        collection_name=collection,
    )

    # Count chunks matching this document_id before delete
    data = store._collection.get(
        where={"document_id": document_id.strip()},
        include=[],
    )
    ids = data.get("ids") or []
    deleted_count = len(ids)

    if ids:
        store._collection.delete(where={"document_id": document_id.strip()})

    return {
        "deleted_chunks": deleted_count,
        "document_id": document_id.strip(),
        "persist_directory": str(persist_path),
        "collection_name": collection,
    }
