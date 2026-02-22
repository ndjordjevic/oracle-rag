"""MCP server setup using FastMCP."""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from oracle_rag.mcp.tools import add_pdf, list_pdfs, query_pdf, remove_pdf

# Load environment variables
load_dotenv()

# Verify required environment variables
if not os.environ.get("OPENAI_API_KEY"):
    print(
        "Warning: OPENAI_API_KEY not set. MCP tools will fail without it.",
        file=sys.stderr,
    )

# Create FastMCP server instance
mcp = FastMCP("Oracle-RAG", json_response=True)


@mcp.tool()
def query_pdf_tool(
    query: str,
    k: int = 5,
    persist_dir: str = "chroma_db",
    collection: str = "oracle_rag",
) -> dict:
    """Query indexed PDFs and return an answer with citations.

    This tool searches through all indexed PDF documents and uses RAG
    (Retrieval-Augmented Generation) to provide an answer based on the
    retrieved context, along with source citations.

    Args:
        query: Natural language question to ask about the indexed PDFs.
        k: Number of document chunks to retrieve (default: 5).
        persist_dir: Chroma vector store persistence directory (default: "chroma_db").
        collection: Chroma collection name (default: "oracle_rag").

    Returns:
        Dictionary containing:
        - answer: The generated answer text
        - sources: List of source citations with document_id and page number
    """
    return query_pdf(query=query, k=k, persist_dir=persist_dir, collection=collection)


@mcp.tool()
def add_pdf_tool(
    pdf_path: str,
    persist_dir: str = "chroma_db",
    collection: str = "oracle_rag",
) -> dict:
    """Add a PDF document to the index.

    This tool processes a PDF file, extracts text, chunks it, generates
    embeddings, and stores it in the vector database for later querying.

    Args:
        pdf_path: Path to the PDF file to index.
        persist_dir: Chroma vector store persistence directory (default: "chroma_db").
        collection: Chroma collection name (default: "oracle_rag").

    Returns:
        Dictionary containing indexing results:
        - source_path: Path to the indexed PDF
        - total_pages: Number of pages processed
        - total_chunks: Number of text chunks created
        - persist_directory: Where the index is stored
        - collection_name: Collection name used
    """
    return add_pdf(pdf_path=pdf_path, persist_dir=persist_dir, collection=collection)


@mcp.tool()
def list_pdfs_tool(
    persist_dir: str = "chroma_db",
    collection: str = "oracle_rag",
) -> dict:
    """List all indexed PDFs (books) in the Oracle-RAG index.

    Returns the unique document names (e.g. PDF file names) currently in the
    vector store, plus total chunk count. Use this to see which books are
    available for querying.

    Args:
        persist_dir: Chroma vector store persistence directory (default: "chroma_db").
        collection: Chroma collection name (default: "oracle_rag").

    Returns:
        Dictionary containing:
        - documents: List of unique document identifiers (typically file names)
        - total_chunks: Total number of chunks in the index
        - persist_directory: Path to the Chroma store
        - collection_name: Collection name used
    """
    return list_pdfs(persist_dir=persist_dir, collection=collection)


@mcp.tool()
def remove_pdf_tool(
    document_id: str,
    persist_dir: str = "chroma_db",
    collection: str = "oracle_rag",
) -> dict:
    """Remove a PDF and all its chunks and embeddings from the Oracle-RAG index.

    Deletes all chunks and their embeddings for the given document from the
    Chroma vector store. Use list_pdfs_tool to see the exact document_id
    (typically the PDF file name) to remove.

    Args:
        document_id: Document identifier to remove (same as in list_pdfs, e.g. "mybook.pdf").
        persist_dir: Chroma vector store persistence directory (default: "chroma_db").
        collection: Chroma collection name (default: "oracle_rag").

    Returns:
        Dictionary containing:
        - deleted_chunks: Number of chunks (and embeddings) removed
        - document_id: The document that was removed
        - persist_directory: Path to the Chroma store
        - collection_name: Collection name used
    """
    return remove_pdf(
        document_id=document_id,
        persist_dir=persist_dir,
        collection=collection,
    )


def create_mcp_server() -> FastMCP:
    """Create and return the configured MCP server instance.

    Returns:
        FastMCP server instance with all tools registered.
    """
    return mcp


if __name__ == "__main__":
    # Entry point for running the server directly
    # Use stdio transport for MCP clients
    mcp.run(transport="stdio")
