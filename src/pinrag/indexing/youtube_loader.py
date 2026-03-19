"""Load YouTube video transcripts into LangChain Documents for RAG indexing."""

from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass

from langchain_core.documents import Document

from pinrag.config import get_yt_proxy_config

# YouTube video ID: 11 alphanumeric chars (base64-like)
_VIDEO_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")
# Playlist: list=PL... (playlist IDs are typically 13-34 chars; allow 2+ for short test IDs)
_PLAYLIST_ID_RE = re.compile(r"[?&]list=([a-zA-Z0-9_-]{2,})", re.IGNORECASE)
_PLAYLIST_URL_RE = re.compile(
    r"youtube\.com/playlist\?list=([a-zA-Z0-9_-]{2,})",
    re.IGNORECASE,
)

# youtube.com/watch?v=VIDEO_ID, youtu.be/VIDEO_ID, youtube.com/embed/VIDEO_ID, etc.
_URL_PATTERNS = [
    re.compile(r"(?:youtube\.com/watch\?.*v=)([a-zA-Z0-9_-]{11})", re.IGNORECASE),
    re.compile(r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})", re.IGNORECASE),
    re.compile(r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})", re.IGNORECASE),
    re.compile(r"(?:youtube\.com/v/)([a-zA-Z0-9_-]{11})", re.IGNORECASE),
]

# Language fallback order for transcript fetch
_DEFAULT_LANGUAGES = ("en", "en-US", "en-GB")


def extract_playlist_id(input_str: str) -> str | None:
    """Extract YouTube playlist ID from URL.

    Supports: youtube.com/playlist?list=PL..., youtube.com/watch?v=X&list=PL...

    Returns:
        Playlist ID string, or None if not a playlist URL.

    """
    s = (input_str or "").strip()
    if not s:
        return None
    s_lower = s.lower()
    if "youtube.com" not in s_lower and "youtu.be" not in s_lower:
        return None
    m = _PLAYLIST_URL_RE.search(s)
    if m:
        return m.group(1)
    m = _PLAYLIST_ID_RE.search(s)
    if m:
        return m.group(1)
    return None


def fetch_playlist_info(playlist_id: str) -> dict:
    """Fetch playlist metadata and video IDs via yt-dlp (no API key, no download).

    Uses extract_flat to get video IDs and titles without downloading.

    Args:
        playlist_id: YouTube playlist ID (e.g. from extract_playlist_id).

    Returns:
        Dict with "playlist_id", "playlist_title", "video_ids" (list of str).

    Raises:
        ValueError: If playlist_id is empty or invalid.
        RuntimeError: If yt-dlp cannot fetch the playlist.

    """
    if not playlist_id or not str(playlist_id).strip():
        raise ValueError("playlist_id cannot be empty")
    playlist_id = str(playlist_id).strip()
    url = f"https://www.youtube.com/playlist?list={playlist_id}"

    import yt_dlp  # type: ignore[import-untyped]

    opts = {
        "flat_playlist": True,
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        raise RuntimeError(
            f"Could not fetch YouTube playlist {playlist_id}: {e}"
        ) from e

    if not info:
        raise RuntimeError(f"Could not fetch YouTube playlist {playlist_id}")

    title = info.get("title") or ""
    entries = info.get("entries") or []
    video_ids: list[str] = []
    for entry in entries:
        if entry is None:
            continue
        vid = entry.get("id")
        if vid and isinstance(vid, str) and len(vid) == 11:
            video_ids.append(vid)

    return {
        "playlist_id": playlist_id,
        "playlist_title": title,
        "video_ids": video_ids,
    }


def extract_video_id(input_str: str) -> str | None:
    """Extract YouTube video ID from URL or raw ID.

    Supports: youtube.com/watch?v=ID, youtu.be/ID, youtube.com/embed/ID,
    youtube.com/v/ID, or a bare 11-char video ID.

    Returns:
        Video ID string, or None if not recognized.

    """
    s = (input_str or "").strip()
    if not s:
        return None
    # Bare video ID
    if _VIDEO_ID_RE.match(s):
        return s
    # URL patterns
    for pat in _URL_PATTERNS:
        m = pat.search(s)
        if m:
            return m.group(1)
    return None


def _canonical_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def _fetch_video_title(video_id: str) -> str | None:
    """Fetch video title via YouTube oEmbed (no API key required).

    Returns title string or None if fetch fails.
    """
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get("title")
    except Exception:
        return None


@dataclass(frozen=True)
class YouTubeLoadResult:
    """Result of loading a YouTube transcript into Documents."""

    video_id: str
    source_url: str
    documents: list[Document]
    total_segments: int
    title: str | None = None


def load_youtube_transcript_as_documents(
    url_or_id: str,
    *,
    languages: tuple[str, ...] = _DEFAULT_LANGUAGES,
    document_id: str | None = None,
) -> YouTubeLoadResult:
    """Load a YouTube video transcript into LangChain Documents.

    Fetches captions via youtube-transcript-api with language fallback.
    Each transcript segment becomes a Document with metadata: document_id,
    video_id, start (seconds), duration, source (canonical URL).

    Args:
        url_or_id: YouTube URL (e.g. https://youtu.be/xyz) or 11-char video ID.
        languages: Language codes to try in order (default: en, en-US, en-GB).
        document_id: Override for document_id. If None, uses video_id.

    Returns:
        YouTubeLoadResult with documents, video_id, source_url, total_segments.

    Raises:
        ValueError: If url_or_id is not a valid YouTube URL or video ID.
        RuntimeError: If transcript cannot be retrieved (disabled, not found, etc.).

    """
    from youtube_transcript_api import (
        NoTranscriptFound,
        TranscriptsDisabled,
        YouTubeTranscriptApi,
    )

    video_id = extract_video_id(url_or_id)
    if not video_id:
        raise ValueError(
            f"Invalid YouTube URL or video ID: {url_or_id!r}. "
            "Expected youtube.com/watch?v=ID, youtu.be/ID, or an 11-char video ID."
        )

    source_url = _canonical_url(video_id)
    doc_id = document_id if document_id else video_id
    title = _fetch_video_title(video_id)

    proxy_config = get_yt_proxy_config()
    api = (
        YouTubeTranscriptApi(proxy_config=proxy_config)
        if proxy_config
        else YouTubeTranscriptApi()
    )
    transcript = None
    last_error: Exception | None = None

    # Try requested languages first
    for lang in languages:
        try:
            transcript = api.fetch(video_id, languages=[lang])
            break
        except (NoTranscriptFound, TranscriptsDisabled) as e:
            last_error = e
            continue

    # Fallback: list transcripts and use first available
    if transcript is None:
        try:
            transcript_list = api.list(video_id)
            # Avoid private attributes from youtube-transcript-api internals.
            transcript = next(iter(transcript_list)).fetch()
        except Exception as e:
            last_error = e

    if transcript is None:
        if last_error is not None:
            if isinstance(last_error, TranscriptsDisabled):
                raise RuntimeError(
                    f"YouTube video {video_id} has transcripts disabled. "
                    "Cannot index this video."
                ) from last_error
            if isinstance(last_error, NoTranscriptFound):
                raise RuntimeError(
                    f"No transcript found for YouTube video {video_id}. "
                    "Try a different video or language."
                ) from last_error
            raise RuntimeError(
                f"Could not retrieve transcript for YouTube video {video_id}: {last_error}"
            ) from last_error
        raise RuntimeError(
            f"Could not retrieve transcript for YouTube video {video_id}. "
            "No transcript available and no error was captured."
        )

    segments = list(transcript)
    documents: list[Document] = []
    for seg in segments:
        text = getattr(seg, "text", "") or ""
        start = getattr(seg, "start", 0) or 0
        duration = getattr(seg, "duration", 0) or 0
        meta: dict = {
            "document_id": doc_id,
            "document_type": "youtube",
            "video_id": video_id,
            "start": int(round(float(start))),
            "duration": round(float(duration), 2),
            "source": source_url,
        }
        if title:
            meta["title"] = title
        documents.append(Document(page_content=str(text).strip(), metadata=meta))

    return YouTubeLoadResult(
        video_id=video_id,
        source_url=source_url,
        documents=documents,
        total_segments=len(segments),
        title=title,
    )
