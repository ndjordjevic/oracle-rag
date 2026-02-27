"""MCP tool implementations that wrap Oracle-RAG functionality."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langsmith import traceable

from oracle_rag.embeddings import get_embedding_model
from oracle_rag.indexing import IndexResult, index_pdf
from oracle_rag.llm import get_chat_model
from oracle_rag.rag import run_rag
from oracle_rag.vectorstore import get_chroma_store
from oracle_rag.vectorstore.chroma_client import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_PERSIST_DIR,
)


@traceable(name="query_pdf", run_type="tool")
def query_pdf(
    query: str,
    k: int = 5,
    persist_dir: str = str(DEFAULT_PERSIST_DIR),
    collection: str = DEFAULT_COLLECTION_NAME,
    document_id: str | None = None,
) -> dict[str, Any]:
    """Query indexed PDFs and return an answer with citations.

    Args:
        query: Natural language question to ask.
        k: Number of chunks to retrieve (default: 5).
        persist_dir: Chroma persistence directory (default: "chroma_db").
        collection: Chroma collection name (default: "oracle_rag").
        document_id: Optional document ID to filter retrieval (e.g. PDF file name from list_pdfs).

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
    if not collection or not str(collection).strip():
        raise ValueError("collection cannot be empty")

    persist_path = Path(persist_dir).expanduser().resolve()
    if not persist_path.exists():
        raise FileNotFoundError(
            f"Persistence directory does not exist: {persist_dir}. "
            "Index some PDFs first using add_pdf."
        )

    embedding = get_embedding_model()
    llm = get_chat_model()

    doc_id_filter = document_id.strip() if document_id and str(document_id).strip() else None
    result = run_rag(
        query,
        llm,
        k=k,
        persist_directory=str(persist_path),
        collection_name=collection,
        embedding=embedding,
        document_id=doc_id_filter,
    )

    return {
        "answer": result.answer,
        "sources": [
            {
                "document_id": str(s.get("document_id", "unknown")),
                "page": int(s.get("page", 0)),
            }
            for s in result.sources
        ],
    }


@traceable(name="add_pdf", run_type="tool")
def add_pdf(
    pdf_path: str,
    persist_dir: str = str(DEFAULT_PERSIST_DIR),
    collection: str = DEFAULT_COLLECTION_NAME,
    tag: str | None = None,
) -> dict[str, Any]:
    """Add a PDF to the index.

    Args:
        pdf_path: Path to the PDF file to index.
        persist_dir: Chroma persistence directory (default: "chroma_db").
        collection: Chroma collection name (default: "oracle_rag").
        tag: Optional single tag for this document (e.g. "amiga"); stored on all chunks for filtering.

    Returns:
        Dictionary with indexing results: source_path, total_pages, total_chunks,
        persist_directory, collection_name.

    Raises:
        FileNotFoundError: If PDF file doesn't exist.
        ValueError: If PDF cannot be processed.
    """
    if not pdf_path or not str(pdf_path).strip():
        raise ValueError("pdf_path cannot be empty")
    if not collection or not str(collection).strip():
        raise ValueError("collection cannot be empty")

    pdf_file = Path(pdf_path).expanduser().resolve()
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if pdf_file.suffix.lower() != ".pdf":
        raise ValueError(f"File is not a PDF: {pdf_path}")

    # Initialize embedding model
    embedding = get_embedding_model()

    # Index the PDF
    result: IndexResult = index_pdf(
        pdf_file,
        persist_directory=persist_dir,
        collection_name=collection,
        embedding=embedding,
        tag=tag.strip() if tag and str(tag).strip() else None,
    )

    # Convert to JSON-serializable format
    return {
        "source_path": str(result.source_path),
        "total_pages": result.total_pages,
        "total_chunks": result.total_chunks,
        "persist_directory": str(result.persist_directory),
        "collection_name": result.collection_name,
    }


@traceable(name="add_pdfs", run_type="tool")
def add_pdfs(
    pdf_paths: list[str],
    persist_dir: str = str(DEFAULT_PERSIST_DIR),
    collection: str = DEFAULT_COLLECTION_NAME,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Add multiple PDFs to the index in one call.

    Continues indexing even if some files fail validation or indexing.

    Args:
        pdf_paths: List of PDF file paths to index.
        persist_dir: Chroma persistence directory (default: "chroma_db").
        collection: Chroma collection name (default: "oracle_rag").
        tags: Optional list of tags, one per PDF (same order as pdf_paths). Empty string = no tag.

    Returns:
        Dictionary containing indexed file results, failed file errors, and totals.

    Raises:
        ValueError: If pdf_paths is empty or collection is invalid.
    """
    if not pdf_paths:
        raise ValueError("pdf_paths cannot be empty")
    if not collection or not str(collection).strip():
        raise ValueError("collection cannot be empty")
    if tags is not None and len(tags) != len(pdf_paths):
        raise ValueError("tags must have same length as pdf_paths when provided")

    embedding = get_embedding_model()
    indexed: list[dict[str, Any]] = []
    failed: list[dict[str, str]] = []

    for i, raw_path in enumerate(pdf_paths):
        try:
            if not raw_path or not str(raw_path).strip():
                raise ValueError("pdf_path cannot be empty")

            pdf_file = Path(raw_path).expanduser().resolve()
            if not pdf_file.exists():
                raise FileNotFoundError(f"PDF file not found: {raw_path}")
            if pdf_file.suffix.lower() != ".pdf":
                raise ValueError(f"File is not a PDF: {raw_path}")

            doc_tag: str | None = None
            if tags is not None and i < len(tags) and tags[i] and str(tags[i]).strip():
                doc_tag = str(tags[i]).strip()
            result: IndexResult = index_pdf(
                pdf_file,
                persist_directory=persist_dir,
                collection_name=collection,
                embedding=embedding,
                tag=doc_tag,
            )
            indexed.append(
                {
                    "source_path": str(result.source_path),
                    "total_pages": result.total_pages,
                    "total_chunks": result.total_chunks,
                }
            )
        except Exception as e:
            failed.append({"pdf_path": str(raw_path), "error": str(e)})

    return {
        "indexed": indexed,
        "failed": failed,
        "total_indexed": len(indexed),
        "total_failed": len(failed),
        "persist_directory": str(Path(persist_dir).expanduser().resolve()),
        "collection_name": collection,
    }


@traceable(name="list_pdfs", run_type="tool")
def list_pdfs(
    persist_dir: str = str(DEFAULT_PERSIST_DIR),
    collection: str = DEFAULT_COLLECTION_NAME,
) -> dict[str, Any]:
    """List all indexed PDFs (books) in the Oracle-RAG index.

    Args:
        persist_dir: Chroma persistence directory (default: "chroma_db").
        collection: Chroma collection name (default: "oracle_rag").

    Returns:
        Dictionary with "documents" (list of unique document IDs, typically file names)
        and "total_chunks" (total number of chunks in the index).
    """
    if not collection or not str(collection).strip():
        raise ValueError("collection cannot be empty")

    persist_path = Path(persist_dir).expanduser().resolve()
    if not persist_path.exists():
        return {
            "documents": [],
            "total_chunks": 0,
            "persist_directory": str(persist_path),
            "collection_name": collection,
            "document_details": {},
        }

    store = get_chroma_store(
        persist_directory=persist_dir,
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


@traceable(name="remove_pdf", run_type="tool")
def remove_pdf(
    document_id: str,
    persist_dir: str = str(DEFAULT_PERSIST_DIR),
    collection: str = DEFAULT_COLLECTION_NAME,
) -> dict[str, Any]:
    """Remove a PDF and all its chunks and embeddings from the Chroma index.

    The document_id must match exactly the name shown in list_pdfs (e.g. the
    PDF file name like "mybook.pdf"). All chunks and their embeddings for that
    document are deleted from the vector store.

    Args:
        document_id: Document identifier to remove (same as in list_pdfs, typically the PDF file name).
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
    if not collection or not str(collection).strip():
        raise ValueError("collection cannot be empty")

    persist_path = Path(persist_dir).expanduser().resolve()
    if not persist_path.exists():
        raise FileNotFoundError(
            f"Persistence directory does not exist: {persist_dir}"
        )

    store = get_chroma_store(
        persist_directory=persist_dir,
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
