"""RAG chain: retrieval, context formatting, prompt, LLM, and response with citations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.retrievers import BaseRetriever
from langsmith import traceable

from oracle_rag.rag.formatting import format_docs, format_sources
from oracle_rag.rag.prompts import RAG_PROMPT
from oracle_rag.vectorstore.chroma_client import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_PERSIST_DIR,
)
from oracle_rag.vectorstore.retriever import create_retriever


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
    retriever: Optional[BaseRetriever] = None,
    k: int = 5,
    persist_directory: PathLike = DEFAULT_PERSIST_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    embedding: Optional[Embeddings] = None,
    document_id: Optional[str] = None,
    page_min: Optional[int] = None,
    page_max: Optional[int] = None,
    tag: Optional[str] = None,
) -> RAGResult:
    """Run a 2-step RAG pipeline: retrieve chunks, format context, prompt LLM, return answer with citations.

    Uses LangChain Retriever (store.as_retriever()). Pass a retriever directly for maximum
    flexibility (e.g. wrapped with reranking), or use legacy params to build one from Chroma.

    Args:
        query: Natural language question to answer.
        llm: Chat model for generation (e.g. from get_chat_model()).
        retriever: Optional BaseRetriever. If provided, used directly; else built from legacy params.
        k: Number of chunks to retrieve (default: 5). Ignored when retriever is provided.
        persist_directory: Chroma persistence directory (used when retriever is None).
        collection_name: Chroma collection name (used when retriever is None).
        embedding: Optional embedding model for retrieval (used when retriever is None).
        document_id: Optional document ID to filter retrieval (e.g. PDF file name).
        page_min: Optional start of page range (inclusive). Use with page_max.
        page_max: Optional end of page range (inclusive). Single page: page_min=64, page_max=64.
        tag: Optional tag to filter retrieval (e.g. "PI_PICO").

    Returns:
        RAGResult with answer (str) and sources (list of {document_id, page}).
    """
    if retriever is not None:
        docs = retriever.invoke(query)
    else:
        retriever = create_retriever(
            k=k,
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding=embedding,
            document_id=document_id,
            page_min=page_min,
            page_max=page_max,
            tag=tag,
        )
        docs = retriever.invoke(query)

    messages = RAG_PROMPT.invoke(
        {"context": format_docs(docs), "question": query}
    ).messages
    response = llm.invoke(messages)
    answer = response.content if hasattr(response, "content") else str(response)
    return RAGResult(answer=answer, sources=format_sources(docs))
