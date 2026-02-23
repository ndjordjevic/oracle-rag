"""Configuration from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from oracle_rag.chunking.splitter import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE

# Ensure .env is loaded when config is first imported
load_dotenv()

DEFAULT_PERSIST_DIR = str(Path.home() / ".oracle-rag" / "chroma_db")


def get_persist_dir() -> str:
    """Return Chroma persist directory from ORACLE_RAG_PERSIST_DIR env var, or ~/.oracle-rag/chroma_db."""
    return os.environ.get("ORACLE_RAG_PERSIST_DIR", DEFAULT_PERSIST_DIR)


def get_chunk_size() -> int:
    """Return chunk size from ORACLE_RAG_CHUNK_SIZE env var, or default (1000)."""
    val = os.environ.get("ORACLE_RAG_CHUNK_SIZE")
    if val is None:
        return DEFAULT_CHUNK_SIZE
    try:
        n = int(val)
        if n < 1:
            return DEFAULT_CHUNK_SIZE
        return n
    except ValueError:
        return DEFAULT_CHUNK_SIZE


def get_chunk_overlap() -> int:
    """Return chunk overlap from ORACLE_RAG_CHUNK_OVERLAP env var, or default (200)."""
    val = os.environ.get("ORACLE_RAG_CHUNK_OVERLAP")
    if val is None:
        return DEFAULT_CHUNK_OVERLAP
    try:
        n = int(val)
        if n < 0:
            return DEFAULT_CHUNK_OVERLAP
        return n
    except ValueError:
        return DEFAULT_CHUNK_OVERLAP
