"""Configuration from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from oracle_rag.chunking.splitter import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE

# Ensure .env is loaded when config is first imported
load_dotenv()

# Use project-local chroma_db so CLI, tools, and MCP all see the same index.
# Override with ORACLE_RAG_PERSIST_DIR for ~/.oracle-rag/chroma_db or custom path.
DEFAULT_PERSIST_DIR = "chroma_db"

# LLM provider: openai | anthropic
DEFAULT_LLM_PROVIDER = "anthropic"
DEFAULT_LLM_MODEL_OPENAI = "gpt-4o-mini"
# Anthropic models (set ORACLE_RAG_LLM_MODEL in .env). See https://docs.anthropic.com/en/docs/about-claude/models
# Default: claude-haiku-4-5 (cheapest, fastest). Others: claude-sonnet-4-6, claude-opus-4-6
DEFAULT_LLM_MODEL_ANTHROPIC = "claude-haiku-4-5"

# Evaluator (LLM-as-judge) provider: openai | anthropic
DEFAULT_EVALUATOR_PROVIDER = "openai"
DEFAULT_EVALUATOR_MODEL_OPENAI = "gpt-4o"
DEFAULT_EVALUATOR_MODEL_OPENAI_CONTEXT = "gpt-4o-mini"
DEFAULT_EVALUATOR_MODEL_ANTHROPIC = "claude-sonnet-4-6"
DEFAULT_EVALUATOR_MODEL_ANTHROPIC_CONTEXT = "claude-haiku-4-5"

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


def get_evaluator_provider() -> str:
    """Return evaluator (LLM-as-judge) provider from ORACLE_RAG_EVALUATOR_PROVIDER env (openai | anthropic)."""
    val = os.environ.get("ORACLE_RAG_EVALUATOR_PROVIDER", DEFAULT_EVALUATOR_PROVIDER)
    p = (val or "").strip().lower()
    if p in ("openai", "anthropic"):
        return p
    return DEFAULT_EVALUATOR_PROVIDER


def get_evaluator_model(*, context_heavy: bool = False) -> str:
    """Return evaluator model for correctness/relevance (context_heavy=False) or groundedness/retrieval (context_heavy=True)."""
    val = os.environ.get(
        "ORACLE_RAG_EVALUATOR_MODEL_CONTEXT" if context_heavy else "ORACLE_RAG_EVALUATOR_MODEL"
    )
    if val and str(val).strip():
        return str(val).strip()
    provider = get_evaluator_provider()
    if provider == "anthropic":
        return (
            DEFAULT_EVALUATOR_MODEL_ANTHROPIC_CONTEXT
            if context_heavy
            else DEFAULT_EVALUATOR_MODEL_ANTHROPIC
        )
    return (
        DEFAULT_EVALUATOR_MODEL_OPENAI_CONTEXT
        if context_heavy
        else DEFAULT_EVALUATOR_MODEL_OPENAI
    )


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
    """Return Chroma persist directory from ORACLE_RAG_PERSIST_DIR env var, or chroma_db (project-local)."""
    return os.environ.get("ORACLE_RAG_PERSIST_DIR", DEFAULT_PERSIST_DIR)


def get_collection_name() -> str:
    """Return Chroma collection name.

    If ORACLE_RAG_COLLECTION_NAME is set, use it. Otherwise return 'oracle_rag'.
    Use a single collection per persist dir; if you switch embedding providers,
    re-index or use a separate ORACLE_RAG_PERSIST_DIR / ORACLE_RAG_COLLECTION_NAME
    to avoid dimension mismatches.
    """
    env_name = os.environ.get("ORACLE_RAG_COLLECTION_NAME")
    if env_name and str(env_name).strip():
        return str(env_name).strip()
    return "oracle_rag"


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


DEFAULT_RETRIEVE_K = 20

# Re-ranking (Cohere Re-Rank): retrieve more, rerank to fewer before LLM
DEFAULT_USE_RERANK = False
DEFAULT_RERANK_RETRIEVE_K = 20
DEFAULT_RERANK_TOP_N = 10


def get_retrieve_k() -> int:
    """Return how many chunks to retrieve (default 20). Used for both rerank on and off."""
    val = os.environ.get("ORACLE_RAG_RETRIEVE_K")
    if val is None:
        return DEFAULT_RETRIEVE_K
    try:
        n = int(val)
        if n < 1:
            return DEFAULT_RETRIEVE_K
        return n
    except ValueError:
        return DEFAULT_RETRIEVE_K


def get_use_rerank() -> bool:
    """Return whether to use Cohere re-ranking. Requires oracle-rag[cohere] and COHERE_API_KEY."""
    val = os.environ.get("ORACLE_RAG_USE_RERANK")
    if val is None or not str(val).strip():
        return DEFAULT_USE_RERANK
    v = str(val).strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    return DEFAULT_USE_RERANK


def get_rerank_retrieve_k() -> int:
    """Return how many chunks the base retriever fetches before reranking. Falls back to ORACLE_RAG_RETRIEVE_K when unset."""
    val = os.environ.get("ORACLE_RAG_RERANK_RETRIEVE_K")
    if val is None:
        return get_retrieve_k()
    try:
        n = int(val)
        if n < 1:
            return get_retrieve_k()
        return n
    except ValueError:
        return get_retrieve_k()


def get_rerank_top_n() -> int:
    """Return how many chunks the reranker returns to the LLM (default 10)."""
    val = os.environ.get("ORACLE_RAG_RERANK_TOP_N")
    if val is None:
        return DEFAULT_RERANK_TOP_N
    try:
        n = int(val)
        if n < 1:
            return DEFAULT_RERANK_TOP_N
        return n
    except ValueError:
        return DEFAULT_RERANK_TOP_N


# Multi-query retrieval: generate query variants via LLM, retrieve per variant, merge
DEFAULT_USE_MULTI_QUERY = False
DEFAULT_MULTI_QUERY_COUNT = 4


def get_use_multi_query() -> bool:
    """Return whether to use multi-query retrieval (3-5 query variants, merge results)."""
    val = os.environ.get("ORACLE_RAG_USE_MULTI_QUERY")
    if val is None or not str(val).strip():
        return DEFAULT_USE_MULTI_QUERY
    v = str(val).strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    return DEFAULT_USE_MULTI_QUERY


def get_multi_query_count() -> int:
    """Return number of alternative queries to generate for multi-query retrieval (default 4)."""
    val = os.environ.get("ORACLE_RAG_MULTI_QUERY_COUNT")
    if val is None:
        return DEFAULT_MULTI_QUERY_COUNT
    try:
        n = int(val)
        if n < 1:
            return DEFAULT_MULTI_QUERY_COUNT
        if n > 10:
            return 10
        return n
    except ValueError:
        return DEFAULT_MULTI_QUERY_COUNT
