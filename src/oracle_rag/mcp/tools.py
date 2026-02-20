"""MCP tool implementations that wrap Oracle-RAG functionality."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langsmith import traceable

from oracle_rag.embeddings import get_embedding_model
from oracle_rag.indexing import IndexResult, index_pdf
from oracle_rag.llm import get_chat_model
from oracle_rag.rag import get_rag_chain
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
) -> dict[str, Any]:
    """Query indexed PDFs and return an answer with citations.

    Args:
        query: Natural language question to ask.
        k: Number of chunks to retrieve (default: 5).
        persist_dir: Chroma persistence directory (default: "chroma_db").
        collection: Chroma collection name (default: "oracle_rag").

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

    # Initialize models
    embedding = get_embedding_model()
    llm = get_chat_model()

    # Get RAG chain and invoke
    chain = get_rag_chain(
        llm,
        persist_directory=str(persist_path),
        collection_name=collection,
        embedding=embedding,
        k=k,
    )

    result = chain.invoke({"query": query, "k": k})

    # Convert to JSON-serializable format
    return {
        "answer": result["answer"],
        "sources": [
            {
                "document_id": str(s.get("document_id", "unknown")),
                "page": int(s.get("page", 0)),
            }
            for s in result.get("sources", [])
        ],
    }


@traceable(name="add_pdf", run_type="tool")
def add_pdf(
    pdf_path: str,
    persist_dir: str = str(DEFAULT_PERSIST_DIR),
    collection: str = DEFAULT_COLLECTION_NAME,
) -> dict[str, Any]:
    """Add a PDF to the index.

    Args:
        pdf_path: Path to the PDF file to index.
        persist_dir: Chroma persistence directory (default: "chroma_db").
        collection: Chroma collection name (default: "oracle_rag").

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
    )

    # Convert to JSON-serializable format
    return {
        "source_path": str(result.source_path),
        "total_pages": result.total_pages,
        "total_chunks": result.total_chunks,
        "persist_directory": str(result.persist_directory),
        "collection_name": result.collection_name,
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
        }

    store = get_chroma_store(
        persist_directory=persist_dir,
        collection_name=collection,
    )
    data = store.get(include=["metadatas"])
    metadatas = data.get("metadatas") or []

    doc_ids: set[str] = set()
    for meta in metadatas:
        if not isinstance(meta, dict):
            continue
        doc_id = (
            meta.get("document_id")
            or meta.get("file_name")
            or meta.get("source")
            or "unknown"
        )
        doc_ids.add(str(doc_id))

    return {
        "documents": sorted(doc_ids),
        "total_chunks": len(metadatas),
        "persist_directory": str(persist_path),
        "collection_name": collection,
    }
