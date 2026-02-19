"""MCP tool implementations that wrap Oracle-RAG functionality."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from oracle_rag.embeddings import get_embedding_model
from oracle_rag.indexing import IndexResult, index_pdf
from oracle_rag.llm import get_chat_model
from oracle_rag.rag import get_rag_chain
from oracle_rag.vectorstore.chroma_client import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_PERSIST_DIR,
)


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
    pdf_file = Path(pdf_path).expanduser().resolve()
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if not pdf_file.suffix.lower() == ".pdf":
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
