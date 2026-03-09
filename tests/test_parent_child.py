"""Tests for parent-child retrieval: config, docstore, indexer, retriever."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from oracle_rag.config import (
    get_child_chunk_size,
    get_parent_chunk_size,
    get_use_parent_child,
)
from oracle_rag.vectorstore.docstore import get_parent_docstore
from oracle_rag.vectorstore.retriever import create_retriever


def test_get_use_parent_child_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without env var, returns False."""
    monkeypatch.delenv("ORACLE_RAG_USE_PARENT_CHILD", raising=False)
    assert get_use_parent_child() is False


def test_get_use_parent_child_true_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """True-like env values return True."""
    for val in ("true", "1", "yes", "on"):
        monkeypatch.setenv("ORACLE_RAG_USE_PARENT_CHILD", val)
        assert get_use_parent_child() is True


def test_get_use_parent_child_false_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """False-like env values return False."""
    for val in ("false", "0", "no", "off"):
        monkeypatch.setenv("ORACLE_RAG_USE_PARENT_CHILD", val)
        assert get_use_parent_child() is False


def test_get_parent_chunk_size_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without env var, returns 2000."""
    monkeypatch.delenv("ORACLE_RAG_PARENT_CHUNK_SIZE", raising=False)
    assert get_parent_chunk_size() == 2000


def test_get_parent_chunk_size_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env var overrides default."""
    monkeypatch.setenv("ORACLE_RAG_PARENT_CHUNK_SIZE", "3000")
    assert get_parent_chunk_size() == 3000


def test_get_child_chunk_size_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without env var, returns 400."""
    monkeypatch.delenv("ORACLE_RAG_CHILD_CHUNK_SIZE", raising=False)
    assert get_child_chunk_size() == 400


def test_get_child_chunk_size_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env var overrides default."""
    monkeypatch.setenv("ORACLE_RAG_CHILD_CHUNK_SIZE", "256")
    assert get_child_chunk_size() == 256


def test_get_parent_docstore_creates_path(tmp_path: Path) -> None:
    """Docstore creates directory at persist_dir/collection_name_parents."""
    persist = tmp_path / "chroma_foo"
    docstore = get_parent_docstore(str(persist), "my_collection")
    parent_dir = persist / "my_collection_parents"
    assert parent_dir.exists()
    assert parent_dir.is_dir()


def test_create_retriever_returns_chroma_when_parent_child_off(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When ORACLE_RAG_USE_PARENT_CHILD=false, create_retriever returns Chroma retriever."""
    monkeypatch.setenv("ORACLE_RAG_USE_PARENT_CHILD", "false")
    persist = tmp_path / "chroma_test"
    persist.mkdir(parents=True)
    with patch("oracle_rag.vectorstore.retriever.get_chroma_store") as mock:
        mock.return_value.as_retriever.return_value = "chroma_retriever"
        ret = create_retriever(
            k=5,
            persist_directory=str(persist),
            collection_name="test_coll",
        )
    assert ret == "chroma_retriever"
    mock.return_value.as_retriever.assert_called_once()


def test_create_retriever_returns_parent_document_retriever_when_on(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When ORACLE_RAG_USE_PARENT_CHILD=true, create_retriever returns ParentDocumentRetriever."""
    from dotenv import load_dotenv

    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set; skipping ParentDocumentRetriever test")

    monkeypatch.setenv("ORACLE_RAG_USE_PARENT_CHILD", "true")
    persist = tmp_path / "chroma_pc"
    persist.mkdir(parents=True)
    ret = create_retriever(
        k=5,
        persist_directory=str(persist),
        collection_name="test_pc",
    )
    from langchain_classic.retrievers import ParentDocumentRetriever

    assert isinstance(ret, ParentDocumentRetriever)
    assert ret.id_key == "doc_id"
    assert ret.search_kwargs["k"] == 5


def test_index_pdf_parent_child_adds_to_chroma_and_docstore(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When ORACLE_RAG_USE_PARENT_CHILD=true, index_pdf adds child chunks to Chroma and parents to docstore."""
    from dotenv import load_dotenv

    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set; skipping parent-child index test")

    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present; skipping parent-child index test")

    monkeypatch.setenv("ORACLE_RAG_USE_PARENT_CHILD", "true")
    persist_dir = tmp_path / "chroma_pc"
    from oracle_rag.indexing import index_pdf
    from oracle_rag.embeddings import get_embedding_model

    result = index_pdf(
        sample_pdf,
        persist_directory=str(persist_dir),
        collection_name="pc_test",
        embedding=get_embedding_model(),
    )
    assert result.total_chunks > 0
    assert (persist_dir / "pc_test_parents").exists()

    from oracle_rag.vectorstore.chroma_client import get_chroma_store

    store = get_chroma_store(
        persist_directory=str(persist_dir),
        collection_name="pc_test",
        embedding=get_embedding_model(),
    )
    coll = store._collection
    count = coll.count()
    assert count > 0

    docstore = get_parent_docstore(str(persist_dir), "pc_test")
    ids = list(docstore.yield_keys())
    assert len(ids) > 0


def test_index_discord_parent_child_adds_to_chroma_and_docstore(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When ORACLE_RAG_USE_PARENT_CHILD=true, index_discord adds child chunks to Chroma and parents to docstore."""
    from dotenv import load_dotenv

    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set; skipping Discord parent-child index test")

    monkeypatch.setenv("ORACLE_RAG_USE_PARENT_CHILD", "true")
    persist_dir = tmp_path / "chroma_discord_pc"
    discord_txt = tmp_path / "sample_discord.txt"
    discord_txt.write_text(
        "Guild: Test Guild\nChannel: test / sample-channel\n"
        "==========================================\n"
        "[1/1/2025 12:00 PM] user1: Hello world\n"
        "[1/1/2025 12:01 PM] user2: Hi there\n"
        "==========================================\nExported 2 messages\n",
        encoding="utf-8",
    )

    from oracle_rag.indexing import index_discord
    from oracle_rag.embeddings import get_embedding_model

    result = index_discord(
        discord_txt,
        persist_directory=str(persist_dir),
        collection_name="discord_pc_test",
        embedding=get_embedding_model(),
    )
    assert result.total_chunks > 0
    assert (persist_dir / "discord_pc_test_parents").exists()

    from oracle_rag.vectorstore.chroma_client import get_chroma_store

    store = get_chroma_store(
        persist_directory=str(persist_dir),
        collection_name="discord_pc_test",
        embedding=get_embedding_model(),
    )
    assert store._collection.count() > 0

    docstore = get_parent_docstore(str(persist_dir), "discord_pc_test")
    assert len(list(docstore.yield_keys())) > 0


def test_index_pdf_flat_mode_unchanged_when_parent_child_off(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When ORACLE_RAG_USE_PARENT_CHILD=false, index_pdf uses original single-level flow (no _parents dir)."""
    from dotenv import load_dotenv

    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set; skipping flat index test")

    monkeypatch.setenv("ORACLE_RAG_USE_PARENT_CHILD", "false")
    repo_root = Path(__file__).resolve().parents[1]
    sample_pdf = repo_root / "data" / "pdfs" / "sample-text.pdf"
    if not sample_pdf.exists():
        pytest.skip("sample PDF not present; skipping flat index test")

    persist_dir = tmp_path / "chroma_flat"
    from oracle_rag.indexing import index_pdf
    from oracle_rag.embeddings import get_embedding_model

    result = index_pdf(
        sample_pdf,
        persist_directory=str(persist_dir),
        collection_name="flat_test",
        embedding=get_embedding_model(),
    )
    assert result.total_chunks > 0
    assert not (persist_dir / "flat_test_parents").exists()
