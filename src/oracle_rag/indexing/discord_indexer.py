"""Index Discord export TXT files into the Chroma vector store."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union

from langchain_core.embeddings import Embeddings

from oracle_rag.config import get_collection_name
from oracle_rag.indexing.discord_loader import (
    _document_id_from_channel_and_path,
    load_discord_export_as_documents,
)
from oracle_rag.vectorstore.chroma_client import (
    DEFAULT_PERSIST_DIR,
    get_chroma_store,
)


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

    return DiscordIndexResult(
        source_path=load_result.source_path,
        total_messages=load_result.total_messages,
        total_chunks=len(load_result.documents),
        persist_directory=Path(persist_directory).expanduser().resolve(),
        collection_name=collection_name,
        document_id=doc_id,
        channel=load_result.channel,
        guild=load_result.guild,
    )


