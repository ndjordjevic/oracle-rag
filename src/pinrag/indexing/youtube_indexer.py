"""Index YouTube video transcripts into the Chroma vector store."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Union

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
from pinrag.indexing.youtube_loader import (
    YouTubeLoadResult,
    extract_playlist_id,
    fetch_playlist_info,
    load_youtube_transcript_as_documents,
)
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
    title: str | None = None


@dataclass(frozen=True)
class YouTubePlaylistIndexResult:
    """Summary of indexing a YouTube playlist into Chroma."""

    playlist_id: str
    playlist_title: str
    indexed: list[YouTubeIndexResult]
    failed: list[dict]
    total_indexed: int
    total_failed: int
    persist_directory: Path
    collection_name: str


def index_youtube(
    url_or_id: str,
    *,
    persist_directory: PathLike = DEFAULT_PERSIST_DIR,
    collection_name: str | None = None,
    embedding: Embeddings | None = None,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    tag: str | None = None,
    extra_metadata: dict | None = None,
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
        extra_metadata: Optional dict of extra metadata (e.g. playlist_id, playlist_title)
            to add to all chunks.

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
            extra_metadata=extra_metadata,
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

        upload_ts = datetime.now(UTC).isoformat()
        doc_total_chunks = len(chunk_docs)
        doc_segments = load_result.total_segments
        doc_bytes = sum(len(d.page_content.encode("utf-8")) for d in load_result.documents)
        for doc in chunk_docs:
            doc.metadata["document_type"] = "youtube"
            doc.metadata["upload_timestamp"] = upload_ts
            doc.metadata["doc_total_chunks"] = doc_total_chunks
            doc.metadata["doc_segments"] = doc_segments
            doc.metadata["doc_bytes"] = doc_bytes
            if load_result.title:
                doc.metadata["doc_title"] = load_result.title
            if tag is not None and str(tag).strip():
                doc.metadata["tag"] = str(tag).strip()
            for k, v in (extra_metadata or {}).items():
                doc.metadata[k] = v

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
    embedding: Embeddings | None,
    tag: str | None,
    respect_structure: bool,
    extra_metadata: dict | None = None,
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

    upload_ts = datetime.now(UTC).isoformat()
    document_id = load_result.video_id
    source_url = load_result.source_url
    doc_bytes = sum(len(d.page_content.encode("utf-8")) for d in load_result.documents)

    all_children: list[Document] = []
    parent_docstore_entries: list[tuple[str, Document]] = []

    for parent in parent_chunks:
        parent_id = str(uuid.uuid4())
        parent.metadata["doc_id"] = parent_id
        parent.metadata["document_id"] = document_id
        parent.metadata["document_type"] = "youtube"
        parent.metadata["upload_timestamp"] = upload_ts
        parent.metadata["doc_segments"] = load_result.total_segments
        parent.metadata["doc_bytes"] = doc_bytes
        parent.metadata["source"] = source_url
        if load_result.title:
            parent.metadata["doc_title"] = load_result.title
        if tag is not None and str(tag).strip():
            parent.metadata["tag"] = str(tag).strip()
        for k, v in (extra_metadata or {}).items():
            parent.metadata[k] = v

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
            c.metadata["doc_bytes"] = doc_bytes
            c.metadata["source"] = source_url
            if load_result.title:
                c.metadata["doc_title"] = load_result.title
            if tag is not None and str(tag).strip():
                c.metadata["tag"] = str(tag).strip()
            for k, v in (extra_metadata or {}).items():
                c.metadata[k] = v
            all_children.append(c)

        parent_docstore_entries.append((parent_id, parent))

    total_chunks = len(all_children)
    for c in all_children:
        c.metadata["doc_total_chunks"] = total_chunks
    for _, parent_doc in parent_docstore_entries:
        parent_doc.metadata["doc_total_chunks"] = total_chunks

    store._collection.delete(where={"document_id": document_id})

    if parent_docstore_entries:
        docstore.mset(parent_docstore_entries)

    batch_size = 100
    for i in range(0, len(all_children), batch_size):
        batch = all_children[i : i + batch_size]
        store.add_documents(batch)

    return total_chunks


def index_youtube_playlist(
    playlist_url: str,
    *,
    persist_directory: PathLike = DEFAULT_PERSIST_DIR,
    collection_name: str | None = None,
    embedding: Embeddings | None = None,
    tag: str | None = None,
) -> YouTubePlaylistIndexResult:
    """Index all videos in a YouTube playlist into Chroma.

    Fetches video IDs via yt-dlp (extract_flat, no API key), then indexes each
    video individually using index_youtube. Each video is a separate document
    with its own document_id (video_id). Parent-child indexing is applied per
    video when PINRAG_USE_PARENT_CHILD is enabled.

    Args:
        playlist_url: YouTube playlist URL (e.g. youtube.com/playlist?list=PL...).
        persist_directory: Chroma persistence directory.
        collection_name: Chroma collection name. If None, uses config default.
        embedding: Optional embedding model; if None, uses default.
        tag: Optional tag for all indexed videos; stored on all chunks.

    Returns:
        YouTubePlaylistIndexResult with indexed videos, failures, and totals.

    """
    playlist_id = extract_playlist_id(playlist_url)
    if not playlist_id:
        raise ValueError(
            f"Invalid YouTube playlist URL: {playlist_url!r}. "
            "Expected youtube.com/playlist?list=PL... or youtube.com/watch?v=X&list=PL..."
        )

    info = fetch_playlist_info(playlist_id)
    playlist_title = info.get("playlist_title") or ""
    video_ids = info.get("video_ids") or []

    if collection_name is None:
        collection_name = get_collection_name()

    persist_path = Path(persist_directory).expanduser().resolve()
    indexed: list[YouTubeIndexResult] = []
    failed: list[dict] = []

    extra = {"playlist_id": playlist_id}
    if playlist_title:
        extra["playlist_title"] = playlist_title

    for video_id in video_ids:
        try:
            result = index_youtube(
                video_id,
                persist_directory=persist_directory,
                collection_name=collection_name,
                embedding=embedding,
                tag=tag,
                extra_metadata=extra,
            )
            indexed.append(result)
        except Exception as e:
            failed.append({"video_id": video_id, "error": str(e)})

    return YouTubePlaylistIndexResult(
        playlist_id=playlist_id,
        playlist_title=playlist_title,
        indexed=indexed,
        failed=failed,
        total_indexed=len(indexed),
        total_failed=len(failed),
        persist_directory=persist_path,
        collection_name=collection_name,
    )
