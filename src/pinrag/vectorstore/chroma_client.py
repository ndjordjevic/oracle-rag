"""Chroma vector store. Persists to a local directory."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from pinrag.embeddings import get_embedding_model


PathLike = Union[str, Path]

DEFAULT_PERSIST_DIR = "chroma_db"
DEFAULT_COLLECTION_NAME = "pinrag"


def get_chroma_store(
    persist_directory: PathLike = DEFAULT_PERSIST_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    embedding: Optional[Embeddings] = None,
) -> Chroma:
    """Return a Chroma vector store with optional persistence.

    Args:
        persist_directory: Directory to persist the Chroma DB (default: chroma_db).
        collection_name: Chroma collection name (default: pinrag).
        embedding: Embedding model; if None, uses get_embedding_model().

    Returns:
        LangChain Chroma vectorstore (add_documents, similarity_search, etc.).
    """
    path = Path(persist_directory).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    emb = embedding if embedding is not None else get_embedding_model()
    return Chroma(
        persist_directory=str(path),
        collection_name=collection_name,
        embedding_function=emb,
    )
