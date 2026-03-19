"""Tests for query preprocessing."""

from __future__ import annotations

from pinrag.rag.query_preprocess import preprocess_query


def test_normalize_whitespace() -> None:
    """Multiple spaces and newlines collapse to single space, strip edges."""
    assert preprocess_query("  what   is   DMA  ") == "what is DMA"
    assert preprocess_query("foo\n\n\nbar") == "foo bar"
    assert preprocess_query("\t  query  \t") == "query"


def test_strip_boilerplate() -> None:
    """Common MCP/agent prefixes are stripped."""
    assert preprocess_query("User question: What is DMA?") == "What is DMA?"
    assert preprocess_query("Query: blitter minterms") == "blitter minterms"
    assert (
        preprocess_query("Question: How does the Copper work?")
        == "How does the Copper work?"
    )
    assert (
        preprocess_query("Answer the following: cookie cut blitter")
        == "cookie cut blitter"
    )
    assert preprocess_query("Search the documents for: CDANG") == "CDANG"


def test_strip_boilerplate_case_insensitive() -> None:
    """Boilerplate stripping is case-insensitive."""
    assert preprocess_query("USER QUESTION: test") == "test"
    assert preprocess_query("query: foo") == "foo"


def test_no_change_when_no_boilerplate() -> None:
    """Query unchanged when no boilerplate matches."""
    assert (
        preprocess_query("What is the Copper danger bit?")
        == "What is the Copper danger bit?"
    )
    assert preprocess_query("blitter minterm logic") == "blitter minterm logic"


def test_empty_or_only_boilerplate_returns_normalized() -> None:
    """Empty input returns empty; only boilerplate returns non-empty if possible."""
    assert preprocess_query("") == ""
    # If we strip everything, we fall back to normalized original
    assert preprocess_query("Query: ") == "Query:"
    assert preprocess_query("   ") == ""


def test_whitespace_only_returns_empty() -> None:
    """Whitespace-only input normalizes to empty string."""
    assert preprocess_query("   \n\t  ") == ""
