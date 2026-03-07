"""Load DiscordChatExporter TXT exports into LangChain Documents for RAG indexing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from langchain_core.documents import Document


PathLike = Union[str, Path]

# DiscordChatExporter message line: [M/D/YYYY H:MM AM/PM] username (pinned)?
_MESSAGE_HEADER_RE = re.compile(
    r"^\[(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s*(?:AM|PM))\]\s+(.+?)(?:\s*\(pinned\))?\s*$",
    re.IGNORECASE,
)

# Header separator (====...)
_HEADER_SEP_RE = re.compile(r"^=+\s*$")

# Block markers
_REACTIONS_MARKER = "{Reactions}"
_ATTACHMENTS_MARKER = "{Attachments}"
_EMBED_MARKER = "{Embed}"

# Unicode emoji ranges (simplified; covers most common)
_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001F9FF"  # Misc Symbols and Pictographs, Emoticons, etc.
    "\U00002702-\U000027B0"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U00002600-\U000026FF"
    "\U00002700-\U000027BF"
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U0001F900-\U0001F9FF"
    "]+",
    re.UNICODE,
)

DEFAULT_WINDOW_SIZE = 15


def _strip_emoji(text: str) -> str:
    """Remove emoji and other symbol characters from text."""
    return _EMOJI_RE.sub("", text).strip()


def _parse_header(lines: list[str]) -> tuple[str, str]:
    """Parse Guild and Channel from header block. Returns (guild, channel)."""
    guild = ""
    channel = ""
    for line in lines:
        if line.startswith("Guild:"):
            guild = line.replace("Guild:", "").strip()
        elif line.startswith("Channel:"):
            channel = line.replace("Channel:", "").strip()
    return guild, channel


def _slug_from_channel(channel: str) -> str:
    """Derive a slug from channel path, e.g. 'amiga / alicia-1200-pcb' -> 'discord-alicia-1200-pcb'."""
    if not channel:
        return "discord-unknown"
    parts = [p.strip() for p in channel.split("/")]
    last = parts[-1] if parts else channel
    slug = re.sub(r"[^\w\-]", "-", last).strip("-").lower() or "discord"
    return f"discord-{slug}"


def _document_id_from_channel_and_path(channel: str, path: Path) -> str:
    """Derive per-file document_id: channel slug + sanitized filename stem.

    Each file gets a unique document_id so incremental exports (e.g. "after 2026-03-06")
    add chunks without replacing the full export. All share the same tag for channel-level
    query filtering.
    """
    base = _slug_from_channel(channel)
    stem = path.stem
    sanitized = re.sub(r"[^\w\-]", "-", stem).strip("-").lower()
    sanitized = re.sub(r"-+", "-", sanitized)  # collapse multiple hyphens
    if not sanitized:
        return base
    return f"{base}--{sanitized}"


def _tag_from_channel(channel: str) -> str:
    """Derive tag from channel, e.g. 'amiga / alicia-1200-pcb' -> 'DISCORD_ALICIA1200'."""
    if not channel:
        return "DISCORD"
    parts = [p.strip() for p in channel.split("/")]
    last = parts[-1] if parts else channel
    tag = re.sub(r"[^\w]", "", last).upper() or "DISCORD"
    return f"DISCORD_{tag}"


@dataclass(frozen=True)
class _ParsedMessage:
    """Single parsed Discord message."""

    timestamp: str
    author: str
    content: str


def _parse_messages(text: str) -> list[_ParsedMessage]:
    """Parse messages from full export text. Strips header, {Reactions}, {Attachments}, {Embed}."""
    lines = text.split("\n")
    messages: list[_ParsedMessage] = []
    i = 0

    # Skip header block (until first message or footer)
    while i < len(lines):
        line = lines[i]
        if _MESSAGE_HEADER_RE.match(line):
            break
        if "Exported" in line and "message" in line.lower():
            return messages  # Footer, no messages
        i += 1

    while i < len(lines):
        line = lines[i]
        match = _MESSAGE_HEADER_RE.match(line)
        if not match:
            i += 1
            continue

        timestamp = match.group(1)
        author = match.group(2).strip()
        i += 1

        content_parts: list[str] = []
        while i < len(lines):
            curr = lines[i]
            # Next message
            if _MESSAGE_HEADER_RE.match(curr):
                break
            # Block markers - skip until next message or next block
            if curr.strip() == _REACTIONS_MARKER:
                i += 1
                while i < len(lines) and not _MESSAGE_HEADER_RE.match(lines[i]) and lines[i].strip() != _ATTACHMENTS_MARKER and lines[i].strip() != _EMBED_MARKER:
                    i += 1
                continue
            if curr.strip() == _ATTACHMENTS_MARKER:
                i += 1
                while i < len(lines) and not _MESSAGE_HEADER_RE.match(lines[i]) and lines[i].strip() not in (_REACTIONS_MARKER, _EMBED_MARKER):
                    i += 1
                continue
            if curr.strip() == _EMBED_MARKER:
                i += 1
                while i < len(lines) and not _MESSAGE_HEADER_RE.match(lines[i]) and lines[i].strip() != _REACTIONS_MARKER and lines[i].strip() != _ATTACHMENTS_MARKER:
                    i += 1
                continue
            # Footer
            if _HEADER_SEP_RE.match(curr) and i + 1 < len(lines) and "Exported" in lines[i + 1]:
                break
            content_parts.append(curr)
            i += 1

        raw_content = "\n".join(content_parts).strip()
        content = _strip_emoji(raw_content)
        if content or author:  # Keep messages with no content (e.g. "Pinned a message.") if they have author
            messages.append(_ParsedMessage(timestamp=timestamp, author=author, content=content))

    return messages


def _format_message_window(messages: list[_ParsedMessage]) -> str:
    """Format a window of messages as readable conversation text."""
    parts: list[str] = []
    for m in messages:
        if m.content:
            parts.append(f"[{m.timestamp}] {m.author}: {m.content}")
        else:
            parts.append(f"[{m.timestamp}] {m.author}")
    return "\n\n".join(parts)


@dataclass(frozen=True)
class DiscordLoadResult:
    """Result of loading a Discord export into Documents."""

    source_path: Path
    guild: str
    channel: str
    documents: list[Document]
    total_messages: int
    total_chunks: int


def load_discord_export_as_documents(
    path: PathLike,
    *,
    window_size: int = DEFAULT_WINDOW_SIZE,
    document_id: Optional[str] = None,
    tag: Optional[str] = None,
) -> DiscordLoadResult:
    """Load a DiscordChatExporter .txt file into LangChain Documents.

    Parses the TXT format (header, messages with [date] author, {Reactions},
    {Attachments}, {Embed} blocks). Strips noise and emoji. Chunks conversation
    into context-preserving windows of N consecutive messages.

    Args:
        path: Path to the .txt export file.
        window_size: Number of consecutive messages per chunk (default 15).
        document_id: Override for document ID. If None, derived from channel
            (e.g. "discord-alicia-1200-pcb").
        tag: Override for tag. If None, derived from channel (e.g. "DISCORD_ALICIA1200").

    Returns:
        DiscordLoadResult with documents, guild, channel, and stats.
    """
    txt_path = Path(path).expanduser().resolve()
    if not txt_path.exists():
        raise FileNotFoundError(f"Discord export not found: {txt_path}")
    if not txt_path.is_file():
        raise ValueError(f"Path is not a file: {txt_path}")
    if txt_path.suffix.lower() != ".txt":
        raise ValueError(f"Expected a .txt file, got: {txt_path.name}")

    raw = txt_path.read_text(encoding="utf-8", errors="replace")
    lines = raw.split("\n")

    # Parse header (first block before messages)
    header_lines: list[str] = []
    for i, line in enumerate(lines):
        if _MESSAGE_HEADER_RE.match(line) or (_HEADER_SEP_RE.match(line) and i > 2):
            break
        header_lines.append(line)
    guild, channel = _parse_header(header_lines)

    doc_id = (
        document_id
        if document_id
        else _document_id_from_channel_and_path(channel, txt_path)
    )
    doc_tag = tag if tag else _tag_from_channel(channel)

    messages = _parse_messages(raw)
    if not messages:
        return DiscordLoadResult(
            source_path=txt_path,
            guild=guild,
            channel=channel,
            documents=[],
            total_messages=0,
            total_chunks=0,
        )

    documents: list[Document] = []
    for start in range(0, len(messages), window_size):
        window = messages[start : start + window_size]
        content = _format_message_window(window)
        first = window[0]
        last = window[-1]
        meta = {
            "source": "discord",
            "file_name": txt_path.name,
            "channel": channel,
            "guild": guild,
            "author": first.author if len(window) == 1 else f"{first.author}..{last.author}",
            "timestamp": first.timestamp,
            "timestamp_end": last.timestamp,
            "document_id": doc_id,
            "tag": doc_tag,
            "chunk_index": len(documents),
            "message_start": start,
            "message_end": start + len(window) - 1,
        }
        documents.append(Document(page_content=content, metadata=meta))

    return DiscordLoadResult(
        source_path=txt_path,
        guild=guild,
        channel=channel,
        documents=documents,
        total_messages=len(messages),
        total_chunks=len(documents),
    )
