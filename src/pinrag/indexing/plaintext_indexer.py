"""Index plain text files into the Chroma vector store."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from langchain_core.embeddings import Embeddings

from pinrag.chunking import chunk_documents
from pinrag.config import (
    get_chunk_overlap,
    get_chunk_size,
    get_collection_name,
    get_plaintext_max_file_bytes,
    get_structure_aware_chunking,
)
from pinrag.indexing.plaintext_loader import (
    PlaintextLoadResult,
    load_plaintext_as_documents,
)
from pinrag.vectorstore.chroma_client import (
    DEFAULT_PERSIST_DIR,
    get_chroma_store,
)

PathLike = str | Path


@dataclass(frozen=True)
class PlaintextIndexResult:
    """Summary of indexing a plain text file into Chroma."""

    source_path: Path
    total_chunks: int
    persist_directory: Path
    collection_name: str
    document_id: str


def index_plaintext(
    path: PathLike,
    *,
    persist_directory: PathLike = DEFAULT_PERSIST_DIR,
    collection_name: str | None = None,
    embedding: Embeddings | None = None,
    tag: str | None = None,
    document_id: str | None = None,
    max_file_bytes: int | None = None,
) -> PlaintextIndexResult:
    """Load, chunk, and index a plain text file into Chroma.

    Uses the plaintext loader to read the file, chunks with configurable size/overlap,
    and adds to the vector store. Replaces any existing chunks for this document_id.
    Files larger than max_file_bytes are skipped (returns 0 chunks, clears existing
    if re-indexing).

    Args:
        path: Path to the .txt file.
        persist_directory: Chroma persistence directory.
        collection_name: Chroma collection name. If None, uses provider-based name.
        embedding: Optional embedding model; if None, uses default.
        tag: Optional tag for this document (stored on all chunks for filtering).
        document_id: Override for document_id. If None, uses path.name.
        max_file_bytes: Skip files larger than this. If None, uses config.

    Returns:
        PlaintextIndexResult with indexing stats.

    """
    if collection_name is None:
        collection_name = get_collection_name()
    respect_structure = get_structure_aware_chunking()
    txt_path = Path(path).expanduser().resolve()
    max_bytes = (
        max_file_bytes if max_file_bytes is not None else get_plaintext_max_file_bytes()
    )

    load_result: PlaintextLoadResult = load_plaintext_as_documents(
        txt_path,
        document_id=document_id,
        max_file_bytes=max_bytes,
    )

    doc_id = document_id or txt_path.name
    if not load_result.documents:
        store = get_chroma_store(
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding=embedding,
        )
        store._collection.delete(where={"document_id": doc_id})
        return PlaintextIndexResult(
            source_path=load_result.source_path,
            total_chunks=0,
            persist_directory=Path(persist_directory).expanduser().resolve(),
            collection_name=collection_name,
            document_id=doc_id,
        )

    doc_id = load_result.documents[0].metadata["document_id"]
    source_str = str(load_result.source_path)

    size = get_chunk_size()
    overlap = get_chunk_overlap()
    chunk_docs = chunk_documents(
        load_result.documents,
        chunk_size=size,
        chunk_overlap=overlap,
        document_id_key="document_id",
        respect_structure=respect_structure,
    )

    store = get_chroma_store(
        persist_directory=persist_directory,
        collection_name=collection_name,
        embedding=embedding,
    )

    doc_bytes = txt_path.stat().st_size
    upload_ts = datetime.now(UTC).isoformat()
    doc_total_chunks = len(chunk_docs)
    for doc in chunk_docs:
        doc.metadata["document_type"] = "plaintext"
        doc.metadata["source"] = source_str
        doc.metadata["upload_timestamp"] = upload_ts
        doc.metadata["doc_bytes"] = doc_bytes
        doc.metadata["doc_total_chunks"] = doc_total_chunks
        if tag is not None and str(tag).strip():
            doc.metadata["tag"] = str(tag).strip()

    store._collection.delete(where={"document_id": doc_id})

    batch_size = 100
    for i in range(0, len(chunk_docs), batch_size):
        batch = chunk_docs[i : i + batch_size]
        store.add_documents(batch)

    return PlaintextIndexResult(
        source_path=load_result.source_path,
        total_chunks=len(chunk_docs),
        persist_directory=Path(persist_directory).expanduser().resolve(),
        collection_name=collection_name,
        document_id=doc_id,
    )
