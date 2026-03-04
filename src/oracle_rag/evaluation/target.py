"""Target function for LangSmith evaluate()."""

from __future__ import annotations

from oracle_rag.config import get_collection_name, get_persist_dir
from oracle_rag.llm import get_chat_model
from oracle_rag.rag import run_rag
from oracle_rag.vectorstore.retriever import create_retriever


def oracle_rag_target(inputs: dict) -> dict:
    """Target function for LangSmith evaluate().

    Accepts dataset inputs (question, document_id, tag, page_min, page_max),
    runs oracle-rag pipeline, returns answer, sources, and documents for evaluators.

    Returns:
        dict with keys: answer, sources, documents.
        documents are the retrieved chunks (for groundedness, retrieval_relevance).
    """
    question = inputs["question"]
    document_id = inputs.get("document_id")
    tag = inputs.get("tag")
    page_min = inputs.get("page_min")
    page_max = inputs.get("page_max")

    llm = get_chat_model()
    retriever = create_retriever(
        k=10,
        persist_directory=get_persist_dir(),
        collection_name=get_collection_name(),
        document_id=document_id,
        page_min=page_min,
        page_max=page_max,
        tag=tag,
    )

    docs = retriever.invoke(question)
    result = run_rag(question, llm, retriever=retriever)

    return {
        "answer": result.answer,
        "sources": result.sources,
        "documents": docs,
    }
