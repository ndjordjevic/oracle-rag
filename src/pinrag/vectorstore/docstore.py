"""Persistent docstore for parent chunks in parent-child retrieval."""

from __future__ import annotations

from pathlib import Path
from typing import Union

from langchain_classic.storage import LocalFileStore
from langchain_classic.storage._lc_store import create_kv_docstore
from langchain_core.documents import Document
from langchain_core.stores import BaseStore

PathLike = Union[str, Path]


def get_parent_docstore(
    persist_directory: PathLike,
    collection_name: str,
) -> BaseStore[str, Document]:
    """Return a persistent docstore for parent chunks alongside the Chroma collection.

    Stored at <persist_directory>/<collection_name>_parents/ so it lives next to
    the Chroma data. Survives process restarts.

    Args:
        persist_directory: Chroma persist directory (e.g. ~/.oracle-rag/chroma_db).
        collection_name: Chroma collection name (e.g. pinrag).

    Returns:
        A key-value store that persists Document objects by ID.
    """
    path = Path(persist_directory).expanduser().resolve() / f"{collection_name}_parents"
    path.mkdir(parents=True, exist_ok=True)
    fs = LocalFileStore(str(path))
    return create_kv_docstore(fs)
