"""Oracle-RAG evaluators for LangSmith experiments.

LLM-as-judge: configurable via ORACLE_RAG_EVALUATOR_PROVIDER (openai | anthropic).
OpenAI: gpt-4o for correctness/relevance, gpt-4o-mini for context-heavy evaluators.
Anthropic: claude-3-5-sonnet for correctness/relevance, claude-3-5-haiku for context-heavy.
Code evaluators have no LLM cost.
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from oracle_rag.config import get_evaluator_model, get_evaluator_provider

# ---------------------------------------------------------------------------
# LLM-as-judge graders (OPENAI_API_KEY or ANTHROPIC_API_KEY)
# ---------------------------------------------------------------------------

_CORRECTNESS_PROMPT = """You are a teacher grading a quiz about technical hardware documentation.
QUESTION: {question}
GROUND TRUTH ANSWER: {reference}
STUDENT ANSWER: {answer}

Grade based ONLY on factual accuracy relative to ground truth.
It is OK if the student answer has more information, as long as it is accurate.
Treat technical synonyms as equivalent (e.g. "bits" and "pixels" for sprite width, "16.7 million" and "16,777,216" for colour depth).
If the student answer covers the key facts from the ground truth, even if worded differently or with additional detail, grade as correct.
Explain your reasoning step by step."""

_RELEVANCE_PROMPT = """You are a teacher grading a quiz.
QUESTION: {question}
STUDENT ANSWER: {answer}

Is the answer concise, relevant, and helpful for the question?
Explain your reasoning step by step."""

_GROUNDEDNESS_PROMPT = """You are a teacher grading a quiz.
FACTS (retrieved documents):
{context}

STUDENT ANSWER: {answer}

Is the answer grounded in the FACTS? Does it hallucinate information not in FACTS?
If there are no FACTS (empty context), judge whether the answer makes unsupported claims.
Explain your reasoning step by step."""

_RETRIEVAL_RELEVANCE_PROMPT = """You are a teacher grading a quiz.
QUESTION: {question}
FACTS (retrieved documents):
{context}

Are the FACTS relevant to the QUESTION? It is OK if some facts are tangential as long
as they contain keywords or semantic meaning related to the question.
If there are no FACTS (empty context), the retrieved docs are not relevant.
Explain your reasoning step by step."""


class _CorrectnessGrade(TypedDict):
    explanation: Annotated[str, "Step-by-step reasoning"]
    correct: Annotated[bool, "True if factually correct"]


class _RelevanceGrade(TypedDict):
    explanation: Annotated[str, "Step-by-step reasoning"]
    relevant: Annotated[bool, "True if answer addresses the question"]


class _GroundednessGrade(TypedDict):
    explanation: Annotated[str, "Step-by-step reasoning"]
    grounded: Annotated[bool, "True if no hallucination beyond the facts"]


class _RetrievalRelevanceGrade(TypedDict):
    explanation: Annotated[str, "Step-by-step reasoning"]
    relevant: Annotated[bool, "True if retrieved docs are relevant"]


def _get_grader_llm(schema: type, *, context_heavy: bool = False) -> BaseChatModel:
    """Return a grader LLM with structured output (OpenAI or Anthropic per config)."""
    provider = get_evaluator_provider()
    model = get_evaluator_model(context_heavy=context_heavy)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        llm = ChatAnthropic(model=model, temperature=0)
    else:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model=model, temperature=0)

    return llm.with_structured_output(schema, method="json_schema", strict=True)


def _get_page_content(doc: object) -> str:
    """Extract page_content from Document or serialized dict."""
    if hasattr(doc, "page_content"):
        return doc.page_content
    if isinstance(doc, dict):
        return doc.get("page_content", "")
    return ""


def _documents_to_context(documents: list) -> str:
    """Join document page_content for grader prompts."""
    return "\n\n".join(_get_page_content(d) for d in (documents or []))


# ---------------------------------------------------------------------------
# LLM-as-judge evaluators (4)
# ---------------------------------------------------------------------------


def correctness(
    inputs: dict, outputs: dict, reference_outputs: dict
) -> dict:
    """Compare outputs['answer'] to reference_outputs['answer']."""
    grader = _get_grader_llm(_CorrectnessGrade)
    content = _CORRECTNESS_PROMPT.format(
        question=inputs.get("question", ""),
        reference=reference_outputs.get("answer", ""),
        answer=outputs.get("answer", ""),
    )
    grade = grader.invoke([HumanMessage(content=content)])
    return {"key": "correctness", "score": int(grade["correct"])}


def relevance(inputs: dict, outputs: dict) -> dict:
    """Compare outputs['answer'] to inputs['question']."""
    grader = _get_grader_llm(_RelevanceGrade, context_heavy=False)
    content = _RELEVANCE_PROMPT.format(
        question=inputs.get("question", ""),
        answer=outputs.get("answer", ""),
    )
    grade = grader.invoke([HumanMessage(content=content)])
    return {"key": "relevance", "score": int(grade["relevant"])}


def groundedness(inputs: dict, outputs: dict) -> dict:
    """Compare outputs['answer'] to outputs['documents']."""
    context = _documents_to_context(outputs.get("documents", []))
    grader = _get_grader_llm(_GroundednessGrade, context_heavy=True)
    content = _GROUNDEDNESS_PROMPT.format(
        context=context or "(No retrieved documents)",
        answer=outputs.get("answer", ""),
    )
    grade = grader.invoke([HumanMessage(content=content)])
    return {"key": "groundedness", "score": int(grade["grounded"])}


def retrieval_relevance(inputs: dict, outputs: dict) -> dict:
    """Compare outputs['documents'] to inputs['question']."""
    documents = outputs.get("documents", [])
    if not documents:
        return {"key": "retrieval_relevance", "score": 0}
    context = _documents_to_context(documents)
    grader = _get_grader_llm(_RetrievalRelevanceGrade, context_heavy=True)
    content = _RETRIEVAL_RELEVANCE_PROMPT.format(
        question=inputs.get("question", ""),
        context=context,
    )
    grade = grader.invoke([HumanMessage(content=content)])
    return {"key": "retrieval_relevance", "score": int(grade["relevant"])}


# ---------------------------------------------------------------------------
# Code evaluators (3)
# ---------------------------------------------------------------------------


def has_sources(inputs: dict, outputs: dict) -> dict:
    """Answer includes at least one source citation."""
    ok = len(outputs.get("sources", [])) > 0
    return {"key": "has_sources", "score": int(ok)}


def answer_not_empty(inputs: dict, outputs: dict) -> dict:
    """Answer is not empty or a failure message."""
    answer = outputs.get("answer", "")
    ok = bool(answer.strip()) and "failed" not in answer.lower()
    return {"key": "answer_not_empty", "score": int(ok)}


def source_in_expected_docs(
    inputs: dict, outputs: dict, reference_outputs: dict
) -> dict:
    """At least one source document_id matches expected documents."""
    expected = set(reference_outputs.get("expected_document_ids", []))
    if not expected:
        return {"key": "source_in_expected_docs", "score": 1}
    actual = {s.get("document_id") for s in outputs.get("sources", [])}
    ok = bool(actual & expected)
    return {"key": "source_in_expected_docs", "score": int(ok)}


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

EVALUATORS = [
    correctness,
    relevance,
    groundedness,
    retrieval_relevance,
    has_sources,
    answer_not_empty,
    source_in_expected_docs,
]
