"""Indexing utilities for Oracle-RAG."""

from oracle_rag.indexing.discord_indexer import DiscordIndexResult, index_discord
from oracle_rag.indexing.discord_loader import (
    DiscordLoadResult,
    load_discord_export_as_documents,
)
from oracle_rag.indexing.pdf_indexer import IndexResult, index_pdf, query_index
from oracle_rag.indexing.youtube_indexer import YouTubeIndexResult, index_youtube
from oracle_rag.indexing.youtube_loader import (
    YouTubeLoadResult,
    extract_video_id,
    load_youtube_transcript_as_documents,
)

__all__ = [
    "DiscordIndexResult",
    "DiscordLoadResult",
    "IndexResult",
    "YouTubeIndexResult",
    "YouTubeLoadResult",
    "extract_video_id",
    "index_discord",
    "index_pdf",
    "index_youtube",
    "load_discord_export_as_documents",
    "load_youtube_transcript_as_documents",
    "query_index",
]

