"""Retriever creation from Chroma vector store."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter

from pinrag.config import (
    get_child_chunk_size,
    get_collection_name,
    get_use_parent_child,
)
from pinrag.vectorstore.chroma_client import (
    DEFAULT_PERSIST_DIR,
    get_chroma_store,
)
from pinrag.vectorstore.docstore import get_parent_docstore


PathLike = Union[str, Path]


def build_retrieval_filter(
    document_id: Optional[str] = None,
    page_min: Optional[int] = None,
    page_max: Optional[int] = None,
    tag: Optional[str] = None,
    document_type: Optional[str] = None,
    file_path: Optional[str] = None,
) -> Optional[dict]:
    """Build Chroma where filter from document_id, page range, tag, document_type, and/or file_path.

    Single page: page_min=64, page_max=64 filters to page 64 only.
    Tag filter returns only chunks with that tag (documents indexed with tag).
    document_type: "pdf", "youtube", "discord", "github", or "plaintext" to filter by source type.
    file_path: For GitHub repos, exact path within the repo (e.g. src/ria/api/atr.c). Use list_documents to see files.
    """
    conditions: list[dict] = []
    if document_id and str(document_id).strip():
        conditions.append({"document_id": document_id.strip()})
    if page_min is not None:
        conditions.append({"page": {"$gte": page_min}})
    if page_max is not None:
        conditions.append({"page": {"$lte": page_max}})
    if tag and str(tag).strip():
        conditions.append({"tag": tag.strip()})
    if document_type and str(document_type).strip():
        conditions.append({"document_type": document_type.strip()})
    if file_path and str(file_path).strip():
        conditions.append({"file_path": file_path.strip()})
    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def create_retriever(
    *,
    k: int = 5,
    persist_directory: PathLike = DEFAULT_PERSIST_DIR,
    collection_name: Optional[str] = None,
    embedding: Optional[Embeddings] = None,
    document_id: Optional[str] = None,
    page_min: Optional[int] = None,
    page_max: Optional[int] = None,
    tag: Optional[str] = None,
    document_type: Optional[str] = None,
    file_path: Optional[str] = None,
) -> BaseRetriever:
    """Create a LangChain retriever from the Chroma vector store.

    Uses store.as_retriever() with search_kwargs for k and metadata filters.
    Compatible with run_rag() and other LangChain components that expect a BaseRetriever.

    Args:
        k: Number of chunks to retrieve (default: 5).
        persist_directory: Chroma persistence directory.
        collection_name: Chroma collection name. If None, uses provider-based name (e.g. pinrag_openai).
        embedding: Optional embedding model; if None, uses default.
        document_id: Optional document ID to filter retrieval.
        page_min: Optional start of page range (inclusive). Use with page_max.
        page_max: Optional end of page range (inclusive).
        tag: Optional tag to filter retrieval.
        document_type: Optional type to filter: "pdf", "youtube", "discord", "github", or "plaintext".
        file_path: Optional file path within a document (GitHub: e.g. src/ria/api/atr.c). Use list_documents to see files.

    Returns:
        BaseRetriever (Chroma retriever with configured search_kwargs).
    """
    if collection_name is None:
        collection_name = get_collection_name()
    store = get_chroma_store(
        persist_directory=persist_directory,
        collection_name=collection_name,
        embedding=embedding,
    )
    filter_dict = build_retrieval_filter(
        document_id=document_id,
        page_min=page_min,
        page_max=page_max,
        tag=tag,
        document_type=document_type,
        file_path=file_path,
    )
    search_kwargs: dict = {"k": k}
    if filter_dict is not None:
        search_kwargs["filter"] = filter_dict

    if get_use_parent_child():
        from langchain_classic.retrievers import ParentDocumentRetriever

        child_size = get_child_chunk_size()
        child_overlap = min(50, child_size // 10)
        child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=child_size,
            chunk_overlap=child_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        docstore = get_parent_docstore(persist_directory, collection_name)
        return ParentDocumentRetriever(
            vectorstore=store,
            docstore=docstore,
            child_splitter=child_splitter,
            parent_splitter=None,
            id_key="doc_id",
            search_kwargs=search_kwargs,
        )

    return store.as_retriever(search_kwargs=search_kwargs)
