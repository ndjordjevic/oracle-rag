"""Format retrieved documents as context and as citation sources."""

from __future__ import annotations

from langchain_core.documents import Document


def format_docs(docs: list[Document], *, number_chunks: bool = True) -> str:
    """Turn a list of chunk documents into a single context string for the prompt.

    Each chunk is separated by newlines. If number_chunks is True, each block
    is prefixed with [N] (doc: <document_id>, p. <page>) so the model and
    users can refer to sources.

    Args:
        docs: Retrieved chunk documents (with metadata such as page, document_id).
        number_chunks: Whether to add [1], [2], ... and doc/page labels.

    Returns:
        A single string suitable for the {context} placeholder in the RAG prompt.
    """
    if not docs:
        return "No relevant context found."

    parts: list[str] = []
    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata
        doc_id = meta.get("document_id") or meta.get("file_name") or meta.get("source") or "?"
        page = meta.get("page", "?")
        if number_chunks:
            parts.append(f"[{i}] (doc: {doc_id}, p. {page})\n{doc.page_content}")
        else:
            parts.append(doc.page_content)

    return "\n\n".join(parts)


def format_sources(docs: list[Document]) -> list[dict[str, str | int]]:
    """Build a list of unique source references from retrieved documents for citations.

    Deduplicates by (document_id, page). Each item has "document_id" and "page".

    Args:
        docs: Retrieved chunk documents.

    Returns:
        List of dicts with keys document_id and page (e.g. for display as "Sources").
    """
    seen: set[tuple[str, int]] = set()
    out: list[dict[str, str | int]] = []
    for doc in docs:
        meta = doc.metadata
        doc_id = str(meta.get("document_id") or meta.get("file_name") or meta.get("source") or "?")
        try:
            page = int(meta.get("page", 0))
        except (TypeError, ValueError):
            page = 0
        key = (doc_id, page)
        if key not in seen:
            seen.add(key)
            out.append({"document_id": doc_id, "page": page})
    return out
