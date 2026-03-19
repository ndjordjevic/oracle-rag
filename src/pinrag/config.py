"""Configuration from environment variables."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pinrag.chunking.splitter import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE

if TYPE_CHECKING:
    from youtube_transcript_api.proxies import GenericProxyConfig

# Use project-local chroma_db so CLI, tools, and MCP all see the same index.
# Override with PINRAG_PERSIST_DIR for ~/.pinrag/chroma_db or custom path.
DEFAULT_PERSIST_DIR = "chroma_db"
DEFAULT_COLLECTION_NAME = "pinrag"

# LLM provider: openai | anthropic
DEFAULT_LLM_PROVIDER = "anthropic"
DEFAULT_LLM_MODEL_OPENAI = "gpt-4o-mini"
# Anthropic models (set PINRAG_LLM_MODEL in .env). See https://docs.anthropic.com/en/docs/about-claude/models
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
    """Return LLM provider from PINRAG_LLM_PROVIDER env (openai | anthropic)."""
    val = os.environ.get("PINRAG_LLM_PROVIDER", DEFAULT_LLM_PROVIDER)
    p = (val or "").strip().lower()
    if p in ("openai", "anthropic"):
        return p
    return DEFAULT_LLM_PROVIDER


def get_llm_model() -> str:
    """Return LLM model name from PINRAG_LLM_MODEL env, or provider default."""
    val = os.environ.get("PINRAG_LLM_MODEL")
    if val and str(val).strip():
        return str(val).strip()
    provider = get_llm_provider()
    if provider == "anthropic":
        return DEFAULT_LLM_MODEL_ANTHROPIC
    return DEFAULT_LLM_MODEL_OPENAI


def get_evaluator_provider() -> str:
    """Return evaluator (LLM-as-judge) provider from PINRAG_EVALUATOR_PROVIDER env (openai | anthropic)."""
    val = os.environ.get("PINRAG_EVALUATOR_PROVIDER", DEFAULT_EVALUATOR_PROVIDER)
    p = (val or "").strip().lower()
    if p in ("openai", "anthropic"):
        return p
    return DEFAULT_EVALUATOR_PROVIDER


def get_evaluator_model(*, context_heavy: bool = False) -> str:
    """Return evaluator model for correctness (context_heavy=False) or groundedness (context_heavy=True)."""
    val = os.environ.get(
        "PINRAG_EVALUATOR_MODEL_CONTEXT" if context_heavy else "PINRAG_EVALUATOR_MODEL"
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
    """Return embedding provider from PINRAG_EMBEDDING_PROVIDER env (openai | cohere)."""
    val = os.environ.get("PINRAG_EMBEDDING_PROVIDER", DEFAULT_EMBEDDING_PROVIDER)
    p = (val or "").strip().lower()
    if p in ("openai", "cohere"):
        return p
    return DEFAULT_EMBEDDING_PROVIDER


def get_embedding_model_name() -> str:
    """Return embedding model name from PINRAG_EMBEDDING_MODEL env, or provider default."""
    val = os.environ.get("PINRAG_EMBEDDING_MODEL")
    if val and str(val).strip():
        return str(val).strip()
    provider = get_embedding_provider()
    if provider == "cohere":
        return DEFAULT_EMBEDDING_MODEL_COHERE
    return DEFAULT_EMBEDDING_MODEL_OPENAI


def get_persist_dir() -> str:
    """Return Chroma persist directory from PINRAG_PERSIST_DIR env var, or chroma_db (project-local)."""
    raw = os.environ.get("PINRAG_PERSIST_DIR")
    if raw is None:
        return DEFAULT_PERSIST_DIR
    s = str(raw).strip()
    return s if s else DEFAULT_PERSIST_DIR


def get_collection_name() -> str:
    """Return Chroma collection name.

    If PINRAG_COLLECTION_NAME is set, use it. Otherwise return DEFAULT_COLLECTION_NAME.
    Use a single collection per persist dir; if you switch embedding providers,
    re-index or use a separate PINRAG_PERSIST_DIR / PINRAG_COLLECTION_NAME
    to avoid dimension mismatches.
    """
    env_name = os.environ.get("PINRAG_COLLECTION_NAME")
    if env_name and str(env_name).strip():
        return str(env_name).strip()
    return DEFAULT_COLLECTION_NAME


def get_chunk_size() -> int:
    """Return chunk size from PINRAG_CHUNK_SIZE env var, or default (1000)."""
    val = os.environ.get("PINRAG_CHUNK_SIZE")
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
    """Return chunk overlap from PINRAG_CHUNK_OVERLAP env var, or default (200).

    If the requested overlap is >= chunk size, clamps to chunk_size - 1 so splitters
    always see overlap < chunk size.
    """
    val = os.environ.get("PINRAG_CHUNK_OVERLAP")
    if val is None:
        return DEFAULT_CHUNK_OVERLAP
    try:
        n = int(val)
        if n < 0:
            return DEFAULT_CHUNK_OVERLAP
        chunk_size = get_chunk_size()
        if n >= chunk_size:
            return max(0, chunk_size - 1)
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
    val = os.environ.get("PINRAG_RETRIEVE_K")
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
    """Return whether to use Cohere re-ranking. Requires pinrag[cohere] and COHERE_API_KEY."""
    val = os.environ.get("PINRAG_USE_RERANK")
    if val is None or not str(val).strip():
        return DEFAULT_USE_RERANK
    v = str(val).strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    return DEFAULT_USE_RERANK


def get_rerank_retrieve_k() -> int:
    """Return how many chunks the base retriever fetches before reranking. Falls back to PINRAG_RETRIEVE_K when unset."""
    val = os.environ.get("PINRAG_RERANK_RETRIEVE_K")
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
    """Return how many chunks the reranker returns to the LLM (default 10).

    Capped by rerank retrieve k so top_n does not exceed the retrieved pool.
    """
    val = os.environ.get("PINRAG_RERANK_TOP_N")
    cap = get_rerank_retrieve_k()
    if val is None:
        return min(DEFAULT_RERANK_TOP_N, cap)
    try:
        n = int(val)
        if n < 1:
            return min(DEFAULT_RERANK_TOP_N, cap)
        return min(n, cap)
    except ValueError:
        return min(DEFAULT_RERANK_TOP_N, cap)


# Multi-query retrieval: generate query variants via LLM, retrieve per variant, merge
DEFAULT_USE_MULTI_QUERY = False
DEFAULT_MULTI_QUERY_COUNT = 4
DEFAULT_MULTI_QUERY_MAX = 10


def get_use_multi_query() -> bool:
    """Return whether to use multi-query retrieval (merged variants; see PINRAG_MULTI_QUERY_COUNT)."""
    val = os.environ.get("PINRAG_USE_MULTI_QUERY")
    if val is None or not str(val).strip():
        return DEFAULT_USE_MULTI_QUERY
    v = str(val).strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    return DEFAULT_USE_MULTI_QUERY


def get_multi_query_count() -> int:
    """Return number of alternative queries for multi-query retrieval (default 4, max 10)."""
    val = os.environ.get("PINRAG_MULTI_QUERY_COUNT")
    if val is None:
        return DEFAULT_MULTI_QUERY_COUNT
    try:
        n = int(val)
        if n < 1:
            return DEFAULT_MULTI_QUERY_COUNT
        if n > DEFAULT_MULTI_QUERY_MAX:
            return DEFAULT_MULTI_QUERY_MAX
        return n
    except ValueError:
        return DEFAULT_MULTI_QUERY_COUNT


# Parent-child retrieval: embed small chunks, return larger parent chunks
DEFAULT_USE_PARENT_CHILD = False
DEFAULT_PARENT_CHUNK_SIZE = 2000
DEFAULT_CHILD_CHUNK_SIZE = 800


def get_use_parent_child() -> bool:
    """Return whether to use parent-child retrieval (embed small, return large chunks)."""
    val = os.environ.get("PINRAG_USE_PARENT_CHILD")
    if val is None or not str(val).strip():
        return DEFAULT_USE_PARENT_CHILD
    v = str(val).strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    return DEFAULT_USE_PARENT_CHILD


def get_parent_chunk_size() -> int:
    """Return parent chunk size in chars for parent-child retrieval (default 2000)."""
    val = os.environ.get("PINRAG_PARENT_CHUNK_SIZE")
    if val is None:
        return DEFAULT_PARENT_CHUNK_SIZE
    try:
        n = int(val)
        if n < 1:
            return DEFAULT_PARENT_CHUNK_SIZE
        return n
    except ValueError:
        return DEFAULT_PARENT_CHUNK_SIZE


def get_child_chunk_size() -> int:
    """Return child chunk size in chars for parent-child retrieval (default 800).

    Never larger than the parent chunk size so parent-child indexing stays consistent.
    """
    parent = get_parent_chunk_size()
    val = os.environ.get("PINRAG_CHILD_CHUNK_SIZE")
    if val is None:
        return min(DEFAULT_CHILD_CHUNK_SIZE, parent)
    try:
        n = int(val)
        if n < 1:
            return min(DEFAULT_CHILD_CHUNK_SIZE, parent)
        return min(n, parent)
    except ValueError:
        return min(DEFAULT_CHILD_CHUNK_SIZE, parent)


# Response style for RAG answer: thorough (default) or concise
DEFAULT_RESPONSE_STYLE = "thorough"
DEFAULT_STRUCTURE_AWARE_CHUNKING = True


def get_response_style() -> str:
    """Return RAG response style from PINRAG_RESPONSE_STYLE (thorough | concise)."""
    val = os.environ.get("PINRAG_RESPONSE_STYLE")
    if val is None or not str(val).strip():
        return DEFAULT_RESPONSE_STYLE
    v = str(val).strip().lower()
    if v in ("thorough", "concise"):
        return v
    return DEFAULT_RESPONSE_STYLE


def get_structure_aware_chunking() -> bool:
    """Return whether to apply structure-aware chunking heuristics (default: true)."""
    val = os.environ.get("PINRAG_STRUCTURE_AWARE_CHUNKING")
    if val is None or not str(val).strip():
        return DEFAULT_STRUCTURE_AWARE_CHUNKING
    v = str(val).strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    return DEFAULT_STRUCTURE_AWARE_CHUNKING


# GitHub repo indexing
DEFAULT_MAX_INDEX_FILE_BYTES = 524288  # 512 KB (shared with plain-text file cap)
DEFAULT_GITHUB_MAX_FILE_BYTES = DEFAULT_MAX_INDEX_FILE_BYTES
DEFAULT_GITHUB_DEFAULT_BRANCH = "main"


def get_github_token() -> str | None:
    """Return GitHub personal access token from GITHUB_TOKEN env (optional)."""
    val = os.environ.get("GITHUB_TOKEN")
    if val and str(val).strip():
        return str(val).strip()
    return None


def get_github_max_file_bytes() -> int:
    """Return max file size in bytes for GitHub indexing (default 512 KB)."""
    val = os.environ.get("PINRAG_GITHUB_MAX_FILE_BYTES")
    if val is None:
        return DEFAULT_GITHUB_MAX_FILE_BYTES
    try:
        n = int(val)
        if n < 1:
            return DEFAULT_GITHUB_MAX_FILE_BYTES
        return n
    except ValueError:
        return DEFAULT_GITHUB_MAX_FILE_BYTES


def get_github_default_branch() -> str:
    """Return default branch for GitHub URLs when not specified (default main)."""
    val = os.environ.get("PINRAG_GITHUB_DEFAULT_BRANCH")
    if val and str(val).strip():
        return str(val).strip()
    return DEFAULT_GITHUB_DEFAULT_BRANCH


# Plain text file indexing
DEFAULT_PLAINTEXT_MAX_FILE_BYTES = DEFAULT_MAX_INDEX_FILE_BYTES


def get_plaintext_max_file_bytes() -> int:
    """Return max file size in bytes for plain text indexing (default 512 KB)."""
    val = os.environ.get("PINRAG_PLAINTEXT_MAX_FILE_BYTES")
    if val is None:
        return DEFAULT_PLAINTEXT_MAX_FILE_BYTES
    try:
        n = int(val)
        if n < 1:
            return DEFAULT_PLAINTEXT_MAX_FILE_BYTES
        return n
    except ValueError:
        return DEFAULT_PLAINTEXT_MAX_FILE_BYTES


def get_yt_proxy_config() -> GenericProxyConfig | None:
    """Return YouTube transcript API proxy config from env, or None if not configured.

    When PINRAG_YT_PROXY_HTTP_URL or PINRAG_YT_PROXY_HTTPS_URL is set, uses
    GenericProxyConfig. Otherwise returns None (no proxy).
    """
    from youtube_transcript_api.proxies import GenericProxyConfig

    http_url = os.environ.get("PINRAG_YT_PROXY_HTTP_URL", "").strip()
    https_url = os.environ.get("PINRAG_YT_PROXY_HTTPS_URL", "").strip()
    if http_url or https_url:
        return GenericProxyConfig(
            http_url=http_url or None,
            https_url=https_url or None,
        )

    return None
