"""Indexing utilities for PinRAG."""

from pinrag.indexing.discord_indexer import DiscordIndexResult, index_discord
from pinrag.indexing.discord_loader import (
    DiscordLoadResult,
    load_discord_export_as_documents,
)
from pinrag.indexing.github_indexer import GitHubIndexResult, index_github
from pinrag.indexing.github_loader import (
    GitHubLoadResult,
    load_github_repo_as_documents,
)
from pinrag.indexing.pdf_indexer import IndexResult, index_pdf, query_index
from pinrag.indexing.youtube_indexer import (
    YouTubeIndexResult,
    YouTubePlaylistIndexResult,
    index_youtube,
    index_youtube_playlist,
)
from pinrag.indexing.youtube_loader import (
    YouTubeLoadResult,
    extract_playlist_id,
    extract_video_id,
    fetch_playlist_info,
    load_youtube_transcript_as_documents,
)

__all__ = [
    "DiscordIndexResult",
    "DiscordLoadResult",
    "GitHubIndexResult",
    "GitHubLoadResult",
    "IndexResult",
    "YouTubeIndexResult",
    "YouTubeLoadResult",
    "YouTubePlaylistIndexResult",
    "extract_playlist_id",
    "extract_video_id",
    "fetch_playlist_info",
    "index_discord",
    "index_github",
    "index_pdf",
    "index_youtube",
    "index_youtube_playlist",
    "load_discord_export_as_documents",
    "load_github_repo_as_documents",
    "load_youtube_transcript_as_documents",
    "query_index",
]

