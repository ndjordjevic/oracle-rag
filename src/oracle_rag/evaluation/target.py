"""Target function for LangSmith evaluate()."""

from __future__ import annotations

from oracle_rag.config import get_collection_name, get_persist_dir, get_response_style
from oracle_rag.llm import get_chat_model
from oracle_rag.rag import run_rag


def oracle_rag_target(inputs: dict) -> dict:
    """Target function for LangSmith evaluate().

    Accepts dataset inputs (question, document_id, page_min, page_max),
    runs oracle-rag pipeline, returns answer, sources, and documents for evaluators.

    Passes retriever=None so run_rag builds the retriever internally — this ensures
    reranking (ORACLE_RAG_USE_RERANK) is applied when enabled.

    Returns:
        dict with keys: answer, sources, documents.
        documents are the retrieved chunks (for groundedness).
    """
    question = inputs["question"]
    document_id = inputs.get("document_id")
    page_min = inputs.get("page_min")
    page_max = inputs.get("page_max")
    # tag is intentionally not forwarded: indexed PDFs don't carry a tag metadata field.

    llm = get_chat_model()
    result = run_rag(
        question,
        llm,
        retriever=None,
        persist_directory=get_persist_dir(),
        collection_name=get_collection_name(),
        document_id=document_id,
        page_min=page_min,
        page_max=page_max,
        response_style=get_response_style(),
    )

    return {
        "answer": result.answer,
        "sources": result.sources,
        "documents": result.documents,
    }
