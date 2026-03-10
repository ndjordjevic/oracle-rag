"""Index YouTube video transcripts into the Chroma vector store."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from pinrag.chunking import chunk_documents
from pinrag.config import (
    get_child_chunk_size,
    get_chunk_overlap,
    get_chunk_size,
    get_collection_name,
    get_parent_chunk_size,
    get_structure_aware_chunking,
    get_use_parent_child,
)
from pinrag.indexing.youtube_loader import YouTubeLoadResult, load_youtube_transcript_as_documents
from pinrag.vectorstore.chroma_client import (
    DEFAULT_PERSIST_DIR,
    get_chroma_store,
)
from pinrag.vectorstore.docstore import get_parent_docstore


PathLike = Union[str, Path]


@dataclass(frozen=True)
class YouTubeIndexResult:
    """Summary of indexing a YouTube video into Chroma."""

    video_id: str
    source_url: str
    total_segments: int
    total_chunks: int
    persist_directory: Path
    collection_name: str
    title: Optional[str] = None


def index_youtube(
    url_or_id: str,
    *,
    persist_directory: PathLike = DEFAULT_PERSIST_DIR,
    collection_name: Optional[str] = None,
    embedding: Optional[Embeddings] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    tag: Optional[str] = None,
) -> YouTubeIndexResult:
    """Load, chunk, and index a YouTube video transcript into Chroma.

    Fetches transcript via youtube-transcript-api, chunks segments, and adds
    to the vector store. Replaces any existing chunks for this video_id.

    Args:
        url_or_id: YouTube URL or 11-char video ID.
        persist_directory: Chroma persistence directory.
        collection_name: Chroma collection name. If None, uses config default.
        embedding: Optional embedding model; if None, uses default.
        chunk_size: Chunk size in chars; if None, uses PINRAG_CHUNK_SIZE.
        chunk_overlap: Chunk overlap in chars; if None, uses PINRAG_CHUNK_OVERLAP.
        tag: Optional tag for this document; stored on all chunks for filtering.

    Returns:
        YouTubeIndexResult with video_id, total_segments, total_chunks, etc.
    """
    if collection_name is None:
        collection_name = get_collection_name()
    respect_structure = get_structure_aware_chunking()
    load_result = load_youtube_transcript_as_documents(url_or_id)
    document_id = load_result.video_id

    if not load_result.documents:
        store = get_chroma_store(
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding=embedding,
        )
        store._collection.delete(where={"document_id": document_id})
        return YouTubeIndexResult(
            video_id=load_result.video_id,
            source_url=load_result.source_url,
            total_segments=0,
            total_chunks=0,
            persist_directory=Path(persist_directory).expanduser().resolve(),
            collection_name=collection_name,
            title=load_result.title,
        )

    if get_use_parent_child():
        total_chunks = _index_youtube_parent_child(
            load_result=load_result,
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding=embedding,
            tag=tag,
            respect_structure=respect_structure,
        )
    else:
        size = chunk_size if chunk_size is not None else get_chunk_size()
        overlap = chunk_overlap if chunk_overlap is not None else get_chunk_overlap()
        chunk_docs = chunk_documents(
            load_result.documents,
            chunk_size=size,
            chunk_overlap=overlap,
            document_id_key="document_id",
            respect_structure=respect_structure,
        )

        upload_ts = datetime.now(timezone.utc).isoformat()
        doc_total_chunks = len(chunk_docs)
        doc_segments = load_result.total_segments
        for doc in chunk_docs:
            doc.metadata["document_type"] = "youtube"
            doc.metadata["upload_timestamp"] = upload_ts
            doc.metadata["doc_total_chunks"] = doc_total_chunks
            doc.metadata["doc_segments"] = doc_segments
            if load_result.title:
                doc.metadata["doc_title"] = load_result.title
            if tag is not None and str(tag).strip():
                doc.metadata["tag"] = str(tag).strip()

        store = get_chroma_store(
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding=embedding,
        )
        store._collection.delete(where={"document_id": document_id})

        batch_size = 100
        for i in range(0, len(chunk_docs), batch_size):
            batch = chunk_docs[i : i + batch_size]
            store.add_documents(batch)
        total_chunks = len(chunk_docs)

    return YouTubeIndexResult(
        video_id=load_result.video_id,
        source_url=load_result.source_url,
        total_segments=load_result.total_segments,
        total_chunks=total_chunks,
        persist_directory=Path(persist_directory).expanduser().resolve(),
        collection_name=collection_name,
        title=load_result.title,
    )


def _index_youtube_parent_child(
    *,
    load_result: YouTubeLoadResult,
    persist_directory: PathLike,
    collection_name: str,
    embedding: Optional[Embeddings],
    tag: Optional[str],
    respect_structure: bool,
) -> int:
    """Index YouTube using parent-child retrieval: embed small chunks, store large parents in docstore."""
    parent_size = get_parent_chunk_size()
    parent_overlap = min(200, parent_size // 10)
    child_size = get_child_chunk_size()
    child_overlap = min(50, child_size // 10)

    # Group segments into parent-sized chunks
    parent_chunks = chunk_documents(
        load_result.documents,
        chunk_size=parent_size,
        chunk_overlap=parent_overlap,
        document_id_key="document_id",
        respect_structure=respect_structure,
    )

    store = get_chroma_store(
        persist_directory=persist_directory,
        collection_name=collection_name,
        embedding=embedding,
    )
    docstore = get_parent_docstore(persist_directory, collection_name)

    upload_ts = datetime.now(timezone.utc).isoformat()
    document_id = load_result.video_id
    source_url = load_result.source_url

    all_children: list[Document] = []
    parent_docstore_entries: list[tuple[str, Document]] = []

    for parent in parent_chunks:
        parent_id = str(uuid.uuid4())
        parent.metadata["doc_id"] = parent_id
        parent.metadata["document_id"] = document_id
        parent.metadata["document_type"] = "youtube"
        parent.metadata["upload_timestamp"] = upload_ts
        parent.metadata["doc_segments"] = load_result.total_segments
        parent.metadata["source"] = source_url
        if load_result.title:
            parent.metadata["doc_title"] = load_result.title
        if tag is not None and str(tag).strip():
            parent.metadata["tag"] = str(tag).strip()

        child_chunks = chunk_documents(
            [parent],
            chunk_size=child_size,
            chunk_overlap=child_overlap,
            document_id_key="document_id",
            respect_structure=respect_structure,
        )
        for c in child_chunks:
            c.metadata["doc_id"] = parent_id
            c.metadata["document_id"] = document_id
            c.metadata["document_type"] = "youtube"
            c.metadata["upload_timestamp"] = upload_ts
            c.metadata["doc_segments"] = load_result.total_segments
            c.metadata["doc_total_chunks"] = len(child_chunks)
            c.metadata["source"] = source_url
            if load_result.title:
                c.metadata["doc_title"] = load_result.title
            if tag is not None and str(tag).strip():
                c.metadata["tag"] = str(tag).strip()
            all_children.append(c)

        parent.metadata["doc_total_chunks"] = len(child_chunks)
        parent_docstore_entries.append((parent_id, parent))

    store._collection.delete(where={"document_id": document_id})

    if parent_docstore_entries:
        docstore.mset(parent_docstore_entries)

    batch_size = 100
    for i in range(0, len(all_children), batch_size):
        batch = all_children[i : i + batch_size]
        store.add_documents(batch)

    return len(all_children)
