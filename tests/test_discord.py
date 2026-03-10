"""Unit tests for Discord loader and indexer."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from pinrag.indexing.discord_loader import (
    DiscordLoadResult,
    _document_id_from_channel_and_path,
    _format_message_window,
    _parse_header,
    _parse_messages,
    _slug_from_channel,
    _strip_emoji,
    _tag_from_channel,
    load_discord_export_as_documents,
)
from pinrag.indexing.discord_indexer import (
    DiscordIndexResult,
    _derive_document_id_from_channel_and_path,
    index_discord,
)


# ---------------------------------------------------------------------------
# discord_loader helpers
# ---------------------------------------------------------------------------


def test_strip_emoji_removes_emoji() -> None:
    assert _strip_emoji("Hello 🌍 World 🎉") == "Hello  World"


def test_strip_emoji_no_emoji() -> None:
    assert _strip_emoji("plain text") == "plain text"


def test_parse_header_extracts_guild_and_channel() -> None:
    lines = ["Guild: My Server", "Channel: amiga / alicia-1200-pcb", "Topic: stuff"]
    guild, channel = _parse_header(lines)
    assert guild == "My Server"
    assert channel == "amiga / alicia-1200-pcb"


def test_parse_header_empty() -> None:
    guild, channel = _parse_header([])
    assert guild == ""
    assert channel == ""


def test_slug_from_channel_normal() -> None:
    assert _slug_from_channel("amiga / alicia-1200-pcb") == "discord-alicia-1200-pcb"


def test_slug_from_channel_empty() -> None:
    assert _slug_from_channel("") == "discord-unknown"


def test_tag_from_channel_normal() -> None:
    assert _tag_from_channel("amiga / alicia-1200-pcb") == "DISCORD_ALICIA1200PCB"


def test_tag_from_channel_empty() -> None:
    assert _tag_from_channel("") == "DISCORD"


def test_document_id_from_channel_and_path() -> None:
    p = Path("/tmp/export-2026-01-01.txt")
    doc_id = _document_id_from_channel_and_path("amiga / alicia-1200-pcb", p)
    assert doc_id.startswith("discord-alicia-1200-pcb--")
    assert "export" in doc_id


def test_document_id_from_channel_and_path_empty_channel() -> None:
    p = Path("/tmp/chat.txt")
    doc_id = _document_id_from_channel_and_path("", p)
    assert doc_id.startswith("discord-unknown--")


# ---------------------------------------------------------------------------
# discord_loader: _parse_messages
# ---------------------------------------------------------------------------

SAMPLE_EXPORT = """\
Guild: Test Server
Channel: general

====================================================

[1/15/2026 10:00 AM] Alice
Hello world

[1/15/2026 10:01 AM] Bob
Hi Alice!

[1/15/2026 10:02 AM] Alice
How are you?
{Reactions}
👍 2

====================================================
Exported 3 message(s)
"""


def test_parse_messages_returns_messages() -> None:
    msgs = _parse_messages(SAMPLE_EXPORT)
    assert len(msgs) == 3
    assert msgs[0].author == "Alice"
    assert msgs[0].content == "Hello world"
    assert msgs[1].author == "Bob"
    assert msgs[2].author == "Alice"
    assert msgs[2].content == "How are you?"


def test_parse_messages_empty() -> None:
    export = "Guild: Test\nChannel: gen\n====\nExported 0 message(s)\n"
    msgs = _parse_messages(export)
    assert msgs == []


# ---------------------------------------------------------------------------
# discord_loader: _format_message_window
# ---------------------------------------------------------------------------


def test_format_message_window() -> None:
    from pinrag.indexing.discord_loader import _ParsedMessage
    msgs = [
        _ParsedMessage(timestamp="1/1/2026 10:00 AM", author="Alice", content="Hi"),
        _ParsedMessage(timestamp="1/1/2026 10:01 AM", author="Bob", content="Hello"),
    ]
    text = _format_message_window(msgs)
    assert "Alice: Hi" in text
    assert "Bob: Hello" in text


# ---------------------------------------------------------------------------
# discord_loader: load_discord_export_as_documents
# ---------------------------------------------------------------------------


def test_load_discord_export_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_discord_export_as_documents("/nonexistent/file.txt")


def test_load_discord_export_wrong_extension(tmp_path: Path) -> None:
    f = tmp_path / "export.pdf"
    f.write_text("dummy")
    with pytest.raises(ValueError, match="Expected a .txt file"):
        load_discord_export_as_documents(f)


def test_load_discord_export_success(tmp_path: Path) -> None:
    f = tmp_path / "export.txt"
    f.write_text(SAMPLE_EXPORT, encoding="utf-8")
    result = load_discord_export_as_documents(f)
    assert isinstance(result, DiscordLoadResult)
    assert result.guild == "Test Server"
    assert result.channel == "general"
    assert result.total_messages == 3
    assert len(result.documents) > 0
    doc = result.documents[0]
    assert doc.metadata["document_type"] == "discord"
    assert doc.metadata["guild"] == "Test Server"


def test_load_discord_export_custom_document_id(tmp_path: Path) -> None:
    f = tmp_path / "export.txt"
    f.write_text(SAMPLE_EXPORT, encoding="utf-8")
    result = load_discord_export_as_documents(f, document_id="my-custom-id")
    assert all(d.metadata["document_id"] == "my-custom-id" for d in result.documents)


def test_load_discord_export_custom_tag(tmp_path: Path) -> None:
    f = tmp_path / "export.txt"
    f.write_text(SAMPLE_EXPORT, encoding="utf-8")
    result = load_discord_export_as_documents(f, tag="MY_TAG")
    assert all(d.metadata["tag"] == "MY_TAG" for d in result.documents)


def test_load_discord_export_empty_messages(tmp_path: Path) -> None:
    f = tmp_path / "export.txt"
    f.write_text(
        "Guild: Test\nChannel: gen\n====\nExported 0 message(s)\n",
        encoding="utf-8",
    )
    result = load_discord_export_as_documents(f)
    assert result.total_messages == 0
    assert result.documents == []


# ---------------------------------------------------------------------------
# discord_indexer: _derive_document_id_from_channel_and_path
# ---------------------------------------------------------------------------


def test_derive_document_id_matches_loader() -> None:
    p = Path("/tmp/chat.txt")
    a = _derive_document_id_from_channel_and_path("amiga / pcb", p)
    b = _document_id_from_channel_and_path("amiga / pcb", p)
    assert a == b


# ---------------------------------------------------------------------------
# discord_indexer: index_discord
# ---------------------------------------------------------------------------


class _MockEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 1536 for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.1] * 1536


def test_index_discord_smoke(tmp_path: Path) -> None:
    """Index a small Discord export; verify result and Chroma contents."""
    export_file = tmp_path / "export.txt"
    export_file.write_text(SAMPLE_EXPORT, encoding="utf-8")
    persist = str(tmp_path / "chroma")

    with patch("pinrag.indexing.discord_indexer.get_use_parent_child", return_value=False):
        result = index_discord(
            export_file,
            persist_directory=persist,
            collection_name="test_discord",
            embedding=_MockEmbeddings(),
        )

    assert isinstance(result, DiscordIndexResult)
    assert result.total_messages == 3
    assert result.total_chunks > 0
    assert result.guild == "Test Server"
    assert result.channel == "general"

    from pinrag.vectorstore import get_chroma_store
    store = get_chroma_store(
        persist_directory=persist,
        collection_name="test_discord",
        embedding=_MockEmbeddings(),
    )
    docs = store.similarity_search("Hello", k=5)
    assert len(docs) > 0
    assert docs[0].metadata.get("document_type") == "discord"


def test_index_discord_replaces_on_reindex(tmp_path: Path) -> None:
    """Indexing same export twice replaces (no duplicate chunks)."""
    export_file = tmp_path / "export.txt"
    export_file.write_text(SAMPLE_EXPORT, encoding="utf-8")
    persist = str(tmp_path / "chroma")
    emb = _MockEmbeddings()

    with patch("pinrag.indexing.discord_indexer.get_use_parent_child", return_value=False):
        r1 = index_discord(
            export_file,
            persist_directory=persist,
            collection_name="test_coll",
            embedding=emb,
        )
        r2 = index_discord(
            export_file,
            persist_directory=persist,
            collection_name="test_coll",
            embedding=emb,
        )

    assert r2.total_chunks == r1.total_chunks


def test_index_discord_empty_export(tmp_path: Path) -> None:
    """Indexing an export with no messages returns 0 chunks."""
    export_file = tmp_path / "export.txt"
    export_file.write_text(
        "Guild: Test\nChannel: gen\n====\nExported 0 message(s)\n",
        encoding="utf-8",
    )
    persist = str(tmp_path / "chroma")

    with patch("pinrag.indexing.discord_indexer.get_use_parent_child", return_value=False):
        result = index_discord(
            export_file,
            persist_directory=persist,
            collection_name="test_coll",
            embedding=_MockEmbeddings(),
        )

    assert result.total_messages == 0
    assert result.total_chunks == 0


def test_index_discord_with_tag(tmp_path: Path) -> None:
    """Tag is propagated to chunk metadata."""
    export_file = tmp_path / "export.txt"
    export_file.write_text(SAMPLE_EXPORT, encoding="utf-8")
    persist = str(tmp_path / "chroma")

    with patch("pinrag.indexing.discord_indexer.get_use_parent_child", return_value=False):
        result = index_discord(
            export_file,
            persist_directory=persist,
            collection_name="test_coll",
            embedding=_MockEmbeddings(),
            tag="AMIGA",
        )

    from pinrag.vectorstore import get_chroma_store
    store = get_chroma_store(
        persist_directory=persist,
        collection_name="test_coll",
        embedding=_MockEmbeddings(),
    )
    docs = store.similarity_search("Hello", k=5)
    assert all(d.metadata.get("tag") == "AMIGA" for d in docs)
