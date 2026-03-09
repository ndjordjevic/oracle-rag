"""Index Discord export TXT files into the Chroma vector store."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from oracle_rag.chunking import chunk_documents
from oracle_rag.config import (
    get_child_chunk_size,
    get_collection_name,
    get_structure_aware_chunking,
    get_use_parent_child,
)
from oracle_rag.indexing.discord_loader import (
    DiscordLoadResult,
    _document_id_from_channel_and_path,
    load_discord_export_as_documents,
)
from oracle_rag.vectorstore.chroma_client import (
    DEFAULT_PERSIST_DIR,
    get_chroma_store,
)
from oracle_rag.vectorstore.docstore import get_parent_docstore


PathLike = Union[str, Path]


@dataclass(frozen=True)
class DiscordIndexResult:
    """Summary of indexing a Discord export into Chroma."""

    source_path: Path
    total_messages: int
    total_chunks: int
    persist_directory: Path
    collection_name: str
    document_id: str
    channel: str
    guild: str


def index_discord(
    path: PathLike,
    *,
    persist_directory: PathLike = DEFAULT_PERSIST_DIR,
    collection_name: Optional[str] = None,
    embedding: Optional[Embeddings] = None,
    tag: Optional[str] = None,
    document_id: Optional[str] = None,
) -> DiscordIndexResult:
    """Load and index a DiscordChatExporter .txt file into Chroma.

    Uses the Discord loader to parse messages into windowed chunks, then adds
    them to the vector store. Replaces any existing chunks for this document_id.

    Args:
        path: Path to the .txt export file.
        persist_directory: Chroma persistence directory.
        collection_name: Chroma collection name. If None, uses provider-based name.
        embedding: Optional embedding model; if None, uses default.
        tag: Optional tag override; if None, derived from channel.
        document_id: Optional document_id override; if None, derived from channel.

    Returns:
        DiscordIndexResult with indexing stats.
    """
    if collection_name is None:
        collection_name = get_collection_name()
    respect_structure = get_structure_aware_chunking()
    txt_path = Path(path).expanduser().resolve()
    load_result = load_discord_export_as_documents(
        txt_path,
        tag=tag,
        document_id=document_id,
    )

    if not load_result.documents:
        doc_id = _document_id_from_channel_and_path(
            load_result.channel, load_result.source_path
        )
        store = get_chroma_store(
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding=embedding,
        )
        store._collection.delete(where={"document_id": doc_id})
        return DiscordIndexResult(
            source_path=load_result.source_path,
            total_messages=0,
            total_chunks=0,
            persist_directory=Path(persist_directory).expanduser().resolve(),
            collection_name=collection_name,
            document_id=doc_id,
            channel=load_result.channel,
            guild=load_result.guild,
        )

    doc_id = load_result.documents[0].metadata["document_id"]

    if get_use_parent_child():
        total_chunks = _index_discord_parent_child(
            load_result=load_result,
            txt_path=txt_path,
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding=embedding,
            tag=tag,
            respect_structure=respect_structure,
        )
    else:
        upload_ts = datetime.now(timezone.utc).isoformat()
        doc_bytes = txt_path.stat().st_size
        doc_total_chunks = len(load_result.documents)

        for doc in load_result.documents:
            doc.metadata["upload_timestamp"] = upload_ts
            doc.metadata["doc_bytes"] = doc_bytes
            doc.metadata["doc_total_chunks"] = doc_total_chunks
            doc.metadata["doc_messages"] = load_result.total_messages
            if tag is not None and str(tag).strip():
                doc.metadata["tag"] = str(tag).strip()

        store = get_chroma_store(
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding=embedding,
        )
        store._collection.delete(where={"document_id": doc_id})

        batch_size = 100
        for i in range(0, len(load_result.documents), batch_size):
            batch = load_result.documents[i : i + batch_size]
            store.add_documents(batch)
        total_chunks = len(load_result.documents)

    return DiscordIndexResult(
        source_path=load_result.source_path,
        total_messages=load_result.total_messages,
        total_chunks=total_chunks,
        persist_directory=Path(persist_directory).expanduser().resolve(),
        collection_name=collection_name,
        document_id=doc_id,
        channel=load_result.channel,
        guild=load_result.guild,
    )


def _index_discord_parent_child(
    *,
    load_result: "DiscordLoadResult",
    txt_path: Path,
    persist_directory: PathLike,
    collection_name: str,
    embedding: Optional[Embeddings],
    tag: Optional[str],
    respect_structure: bool,
) -> int:
    """Index Discord using parent-child retrieval: embed small chunks, store large parents in docstore."""
    child_size = get_child_chunk_size()
    child_overlap = min(50, child_size // 10)

    store = get_chroma_store(
        persist_directory=persist_directory,
        collection_name=collection_name,
        embedding=embedding,
    )
    docstore = get_parent_docstore(persist_directory, collection_name)

    upload_ts = datetime.now(timezone.utc).isoformat()
    doc_bytes = txt_path.stat().st_size
    document_id = load_result.documents[0].metadata["document_id"]
    source_path_str = str(txt_path)

    all_children: list[Document] = []
    parent_docstore_entries: list[tuple[str, Document]] = []

    for parent in load_result.documents:
        parent_id = str(uuid.uuid4())
        parent.metadata["doc_id"] = parent_id
        parent.metadata["document_id"] = document_id
        parent.metadata["upload_timestamp"] = upload_ts
        parent.metadata["doc_bytes"] = doc_bytes
        parent.metadata["doc_messages"] = load_result.total_messages
        parent.metadata["source"] = source_path_str
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
            c.metadata["upload_timestamp"] = upload_ts
            c.metadata["doc_bytes"] = doc_bytes
            c.metadata["doc_messages"] = load_result.total_messages
            c.metadata["doc_total_chunks"] = len(child_chunks)
            c.metadata["source"] = source_path_str
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


