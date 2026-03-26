"""Persistent docstore for parent chunks in parent-child retrieval."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_classic.storage import LocalFileStore, create_kv_docstore
from langchain_core.documents import Document
from langchain_core.stores import BaseStore

PathLike = str | Path


def get_parent_docstore(
    persist_directory: PathLike,
    collection_name: str,
) -> BaseStore[str, Document]:
    """Return a persistent docstore for parent chunks alongside the Chroma collection.

    Stored at <persist_directory>/<collection_name>_parents/ so it lives next to
    the Chroma data. Survives process restarts.

    Args:
        persist_directory: Chroma persist directory (e.g. ~/.pinrag/chroma_db).
        collection_name: Chroma collection name (e.g. pinrag).

    Returns:
        A key-value store that persists Document objects by ID.

    """
    path = Path(persist_directory).expanduser().resolve() / f"{collection_name}_parents"
    path.mkdir(parents=True, exist_ok=True)
    fs = LocalFileStore(str(path))
    return create_kv_docstore(fs)


def remove_parent_docs_for_document(
    *,
    store: Any,
    docstore: BaseStore[str, Document],
    document_id: str,
) -> int:
    """Delete parent-docstore entries referenced by child chunks of a document_id.

    Returns the number of parent IDs removed from docstore.
    """
    data = store.get(where={"document_id": document_id}, include=["metadatas"])
    metadatas = data.get("metadatas") or []
    parent_ids = sorted(
        {
            str(meta["doc_id"])
            for meta in metadatas
            if isinstance(meta, dict) and meta.get("doc_id")
        }
    )
    if parent_ids:
        docstore.mdelete(parent_ids)
    return len(parent_ids)
