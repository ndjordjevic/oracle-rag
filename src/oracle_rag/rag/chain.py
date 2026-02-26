"""RAG chain: retrieval, context formatting, prompt, LLM, and response with citations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langsmith import traceable

from oracle_rag.indexing.pdf_indexer import query_index
from oracle_rag.rag.formatting import format_docs, format_sources
from oracle_rag.rag.prompts import RAG_PROMPT
from oracle_rag.vectorstore.chroma_client import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_PERSIST_DIR,
)


PathLike = Union[str, Path]


@dataclass
class RAGResult:
    """Result of running the RAG chain: answer text and source citations."""

    answer: str
    sources: list[dict[str, str | int]]


@traceable(name="run_rag", run_type="chain")
def run_rag(
    query: str,
    llm: BaseChatModel,
    *,
    k: int = 5,
    persist_directory: PathLike = DEFAULT_PERSIST_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    embedding: Optional[Embeddings] = None,
) -> RAGResult:
    """Run a 2-step RAG pipeline: retrieve chunks, format context, prompt LLM, return answer with citations.

    Plain Python implementation (no LCEL). Uses @traceable for LangSmith per-step tracing.

    Args:
        query: Natural language question to answer.
        llm: Chat model for generation (e.g. from get_chat_model()).
        k: Number of chunks to retrieve (default: 5).
        persist_directory: Chroma persistence directory (must match indexing).
        collection_name: Chroma collection name (must match indexing).
        embedding: Optional embedding model for retrieval; if None, uses default.

    Returns:
        RAGResult with answer (str) and sources (list of {document_id, page}).
    """
    docs = query_index(
        query,
        k=k,
        persist_directory=persist_directory,
        collection_name=collection_name,
        embedding=embedding,
    )
    messages = RAG_PROMPT.invoke(
        {"context": format_docs(docs), "question": query}
    ).messages
    response = llm.invoke(messages)
    answer = response.content if hasattr(response, "content") else str(response)
    return RAGResult(answer=answer, sources=format_sources(docs))
