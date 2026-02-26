"""RAG chain: retrieval-augmented generation with citations."""

from oracle_rag.rag.chain import RAGResult, run_rag
from oracle_rag.rag.formatting import format_docs, format_sources
from oracle_rag.rag.prompts import RAG_PROMPT

__all__ = [
    "RAGResult",
    "RAG_PROMPT",
    "format_docs",
    "format_sources",
    "run_rag",
]
