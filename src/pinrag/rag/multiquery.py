"""Multi-query retrieval: generate query variants via LLM, retrieve per variant, merge results."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain_core.prompts import PromptTemplate
from langchain_core.retrievers import BaseRetriever

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)


def _get_multiquery_prompt(num_queries: int) -> PromptTemplate:
    """Build a prompt that requests exactly num_queries alternative questions."""
    return PromptTemplate(
        input_variables=["question"],
        template=f"""You are an expert at rewriting questions for vector search.

Generate {num_queries} different versions of the following question. Each version should:
- Use different wording or phrasing
- Focus on different aspects or angles of the question
- Be suitable for finding relevant documents in a technical knowledge base

Original question: {{question}}

Return one question per line. Do not number or bullet the questions.""",
    )


def wrap_retriever_with_multiquery(
    base_retriever: BaseRetriever,
    llm: BaseChatModel,
    *,
    include_original: bool = True,
    num_queries: int = 4,
    verbose: bool = False,
) -> BaseRetriever:
    """Wrap a base retriever with multi-query retrieval.

    Generates N differently worded variants of the user query via LLM, runs
    retrieval per variant, merges results (unique union), and returns the
    combined documents. Improves recall for terse or ambiguous queries.

    Args:
        base_retriever: Retriever that fetches chunks per query (e.g. Chroma).
        llm: Chat model for generating query variants.
        include_original: Include the original query in the set of queries (default True).
        num_queries: Number of alternative queries to generate (default 4).
        verbose: Log generated queries (default False).

    Returns:
        BaseRetriever that invokes base_retriever for each query variant and merges results.

    """
    from langchain_classic.retrievers.multi_query import MultiQueryRetriever

    retriever_prompt = _get_multiquery_prompt(num_queries)
    mq_retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm,
        prompt=retriever_prompt,
        include_original=include_original,
    )
    mq_retriever.verbose = verbose
    return mq_retriever
