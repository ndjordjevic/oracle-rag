"""RAG chain: retrieval, context formatting, prompt, LLM, and response with citations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

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


def get_rag_chain(
    llm: BaseChatModel,
    *,
    persist_directory: PathLike = DEFAULT_PERSIST_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    embedding: Optional[Embeddings] = None,
    k: int = 5,
):
    """Build a RAG chain using RunnablePassthrough: retrieve, format context, prompt, generate, add citations.

    Chain input: dict with "query" (str) and optional "k" (int).
    Chain output: dict with "answer" (str) and "sources" (list of {document_id, page}).

    Args:
        llm: Chat model for generation (e.g. from get_chat_model()).
        persist_directory: Chroma persistence directory (must match indexing).
        collection_name: Chroma collection name (must match indexing).
        embedding: Optional embedding model for retrieval; if None, uses default.
        k: Default number of chunks to retrieve.

    Returns:
        A runnable that accepts {"query": str, "k": int?} and returns {"answer": str, "sources": [...]}.
    """

    def retrieve(state: dict[str, Any]) -> list[Document]:
        return query_index(
            state["query"],
            k=state.get("k", k),
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding=embedding,
        )

    # Assign documents first so context/question can use them in the next step.
    chain = (
        RunnablePassthrough.assign(documents=retrieve)
        | RunnablePassthrough.assign(
            context=lambda x: format_docs(x["documents"]),
            question=lambda x: x["query"],
        )
        | RunnablePassthrough.assign(
            answer=RAG_PROMPT | llm | StrOutputParser(),
        )
        | RunnableLambda(
            lambda x: {
                "answer": x["answer"],
                "sources": format_sources(x["documents"]),
            }
        )
    )
    return chain
