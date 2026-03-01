"""Configuration from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from oracle_rag.chunking.splitter import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE

# Ensure .env is loaded when config is first imported
load_dotenv()

DEFAULT_PERSIST_DIR = str(Path.home() / ".oracle-rag" / "chroma_db")

# LLM provider: openai | anthropic
DEFAULT_LLM_PROVIDER = "openai"
DEFAULT_LLM_MODEL_OPENAI = "gpt-4o-mini"
# Anthropic models (set ORACLE_RAG_LLM_MODEL in .env). See https://docs.anthropic.com/en/docs/about-claude/models
# Default: claude-haiku-4-5 (cheapest, fastest). Others: claude-sonnet-4-6, claude-opus-4-6
DEFAULT_LLM_MODEL_ANTHROPIC = "claude-haiku-4-5"

# Embedding provider: openai | cohere
DEFAULT_EMBEDDING_PROVIDER = "openai"
DEFAULT_EMBEDDING_MODEL_OPENAI = "text-embedding-3-small"
DEFAULT_EMBEDDING_MODEL_COHERE = "embed-english-v3.0"


def get_llm_provider() -> str:
    """Return LLM provider from ORACLE_RAG_LLM_PROVIDER env (openai | anthropic)."""
    val = os.environ.get("ORACLE_RAG_LLM_PROVIDER", DEFAULT_LLM_PROVIDER)
    p = (val or "").strip().lower()
    if p in ("openai", "anthropic"):
        return p
    return DEFAULT_LLM_PROVIDER


def get_llm_model() -> str:
    """Return LLM model name from ORACLE_RAG_LLM_MODEL env, or provider default."""
    val = os.environ.get("ORACLE_RAG_LLM_MODEL")
    if val and str(val).strip():
        return str(val).strip()
    provider = get_llm_provider()
    if provider == "anthropic":
        return DEFAULT_LLM_MODEL_ANTHROPIC
    return DEFAULT_LLM_MODEL_OPENAI


def get_embedding_provider() -> str:
    """Return embedding provider from ORACLE_RAG_EMBEDDING_PROVIDER env (openai | cohere)."""
    val = os.environ.get("ORACLE_RAG_EMBEDDING_PROVIDER", DEFAULT_EMBEDDING_PROVIDER)
    p = (val or "").strip().lower()
    if p in ("openai", "cohere"):
        return p
    return DEFAULT_EMBEDDING_PROVIDER


def get_embedding_model_name() -> str:
    """Return embedding model name from ORACLE_RAG_EMBEDDING_MODEL env, or provider default."""
    val = os.environ.get("ORACLE_RAG_EMBEDDING_MODEL")
    if val and str(val).strip():
        return str(val).strip()
    provider = get_embedding_provider()
    if provider == "cohere":
        return DEFAULT_EMBEDDING_MODEL_COHERE
    return DEFAULT_EMBEDDING_MODEL_OPENAI


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
