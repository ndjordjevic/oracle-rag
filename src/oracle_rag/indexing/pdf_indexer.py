"""Index PDF documents into the Chroma vector store."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from oracle_rag.chunking import chunk_documents
from oracle_rag.config import get_chunk_overlap, get_chunk_size
from oracle_rag.pdf.pypdf_loader import PathLike, load_pdf_as_documents
from oracle_rag.vectorstore.chroma_client import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_PERSIST_DIR,
    get_chroma_store,
)


PathLike = Union[str, Path]


@dataclass(frozen=True)
class IndexResult:
    """Summary of indexing a single PDF into Chroma."""

    source_path: Path
    total_pages: int
    total_chunks: int
    persist_directory: Path
    collection_name: str


def index_pdf(
    path: PathLike,
    *,
    persist_directory: PathLike = DEFAULT_PERSIST_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    embedding: Optional[Embeddings] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> IndexResult:
    """Load, chunk, and index a single PDF into Chroma.

    Steps:
    - Load per-page `Document`s via `load_pdf_as_documents`.
    - Chunk them with `chunk_documents`.
    - Get (or create) a Chroma store via `get_chroma_store`.
    - Delete any existing chunks for this document (by file name) to avoid duplicates.
    - Add chunk documents to the store (embeddings generated automatically).

    Args:
        path: PDF path to index.
        persist_directory: Chroma persistence directory.
        collection_name: Chroma collection name.
        embedding: Optional embedding model; if None, uses default OpenAI embeddings.
        chunk_size: Chunk size in chars; if None, uses ORACLE_RAG_CHUNK_SIZE env or 1000.
        chunk_overlap: Chunk overlap in chars; if None, uses ORACLE_RAG_CHUNK_OVERLAP env or 200.

    Returns:
        IndexResult with basic stats about the indexed PDF.
    """
    pdf_path = Path(path).expanduser().resolve()
    pdf_result = load_pdf_as_documents(pdf_path)

    # Turn per-page documents into chunk documents (preserving metadata).
    size = chunk_size if chunk_size is not None else get_chunk_size()
    overlap = chunk_overlap if chunk_overlap is not None else get_chunk_overlap()
    chunk_docs: list[Document] = chunk_documents(
        pdf_result.documents,
        chunk_size=size,
        chunk_overlap=overlap,
    )

    # Get/create the Chroma store.
    store = get_chroma_store(
        persist_directory=persist_directory,
        collection_name=collection_name,
        embedding=embedding,
    )

    # Add document-level metadata to each chunk (upload time, size stats).
    doc_bytes = pdf_path.stat().st_size
    upload_ts = datetime.now(timezone.utc).isoformat()
    doc_pages = pdf_result.total_pages
    doc_total_chunks = len(chunk_docs)
    for doc in chunk_docs:
        doc.metadata["upload_timestamp"] = upload_ts
        doc.metadata["doc_pages"] = doc_pages
        doc.metadata["doc_bytes"] = doc_bytes
        doc.metadata["doc_total_chunks"] = doc_total_chunks

    # Replace existing chunks for this document to avoid duplicates.
    document_id = pdf_path.name
    store._collection.delete(where={"document_id": document_id})

    # Add in batches to avoid OpenAI/Chroma batch size limits (e.g. token or record limits)
    batch_size = 100
    if chunk_docs:
        for i in range(0, len(chunk_docs), batch_size):
            batch = chunk_docs[i : i + batch_size]
            store.add_documents(batch)

    return IndexResult(
        source_path=pdf_result.source_path,
        total_pages=pdf_result.total_pages,
        total_chunks=len(chunk_docs),
        persist_directory=Path(persist_directory).expanduser().resolve(),
        collection_name=collection_name,
    )


def query_index(
    query: str,
    *,
    k: int = 5,
    persist_directory: PathLike = DEFAULT_PERSIST_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    embedding: Optional[Embeddings] = None,
) -> list[Document]:
    """Run a similarity search over the indexed chunks in Chroma.

    Args:
        query: Natural language query string.
        k: Number of top matching chunks to return.
        persist_directory: Chroma persistence directory (must match indexing).
        collection_name: Chroma collection name (must match indexing).
        embedding: Optional embedding model; if None, uses default OpenAI embeddings.

    Returns:
        List of matching chunk `Document`s from the vector store.
    """

    store = get_chroma_store(
        persist_directory=persist_directory,
        collection_name=collection_name,
        embedding=embedding,
    )
    return store.similarity_search(query, k=k)

