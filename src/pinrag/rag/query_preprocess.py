"""Query preprocessing before retrieval: normalize whitespace, strip MCP/agent boilerplate."""

from __future__ import annotations

import re

# Common prefixes/phrases that MCP or agent tools may prepend to the user query.
# Stripped case-insensitively from the start of the query.
_BOILERPLATE_PATTERN = (
    r"^\s*(?:"
    r"Answer the following:\s*|"
    r"User question:\s*|"
    r"Query:\s*|"
    r"Question:\s*|"
    r"Search (?:the )?documents? for:\s*|"
    r"Find (?:in|from) (?:the )?documents?:\s*|"
    r"Look up (?:in|in the documents):\s*"
    r")+"
)
_BOILERPLATE_RE = re.compile(_BOILERPLATE_PATTERN, re.IGNORECASE)


def preprocess_query(query: str) -> str:
    """Normalize and clean the query before retrieval.

    - Collapse runs of whitespace to a single space, strip leading/trailing.
    - Strip common MCP/agent boilerplate prefixes (e.g. "User question:", "Query:").

    The result is used for retrieval; the original query is kept for the prompt
    so the model answers the user's exact wording.

    Args:
        query: Raw user query string.

    Returns:
        Cleaned query string. For empty input, returns an empty string. For non-empty input,
        if stripping boilerplate yields empty, returns the normalized original query.
    """
    if not isinstance(query, str):
        return ""
    if not query:
        return ""
    normalized = " ".join(query.split())
    stripped = _BOILERPLATE_RE.sub("", normalized).strip()
    return stripped if stripped else normalized
