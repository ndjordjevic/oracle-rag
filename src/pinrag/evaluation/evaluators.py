"""PinRAG evaluators for LangSmith experiments.

LLM-as-judge (correctness, groundedness): PINRAG_EVALUATOR_PROVIDER (openai | anthropic | openrouter).
OpenAI: gpt-4o for correctness, gpt-4o-mini for groundedness.
Anthropic: claude-sonnet-4-6 for correctness, claude-haiku-4-5 for groundedness.
OpenRouter: default ``openrouter/free`` for both (zero-cost; the gateway may route across
capable free models). Graders use ``json_schema`` strict structured output—if a routed model
does not support that well, set ``PINRAG_EVALUATOR_MODEL`` / ``PINRAG_EVALUATOR_MODEL_CONTEXT`` to a
specific free slug from https://openrouter.ai/models (filter ``structured_outputs``).
``PINRAG_OPENROUTER_MODEL_FALLBACKS``, ``PINRAG_OPENROUTER_SORT``, and
``PINRAG_OPENROUTER_PROVIDER_ORDER`` apply to the OpenRouter chat client here the same as
for RAG generation when the evaluator provider is openrouter.
Code evaluators have no LLM cost.
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict, cast

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from pinrag.config import (
    get_evaluator_model,
    get_evaluator_provider,
    get_llm_model_fallbacks,
    get_openrouter_app_title,
    get_openrouter_app_url,
    get_openrouter_provider_order,
    get_openrouter_sort,
)

# ---------------------------------------------------------------------------
# LLM-as-judge graders (OPENAI_API_KEY, ANTHROPIC_API_KEY, or OPENROUTER_API_KEY)
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

_GROUNDEDNESS_PROMPT = """You are a teacher grading a quiz.
FACTS (retrieved documents):
{context}

STUDENT ANSWER: {answer}

Is the answer grounded in the FACTS? Does it hallucinate information not in FACTS?
If there are no FACTS (empty context), judge whether the answer makes unsupported claims.
Explain your reasoning step by step."""


class _CorrectnessGrade(TypedDict):
    explanation: Annotated[str, "Step-by-step reasoning"]
    correct: Annotated[bool, "True if factually correct"]


class _GroundednessGrade(TypedDict):
    explanation: Annotated[str, "Step-by-step reasoning"]
    grounded: Annotated[bool, "True if no hallucination beyond the facts"]


def _get_grader_llm(schema: type, *, context_heavy: bool = False) -> Any:
    """Return a grader runnable with structured output (OpenAI, Anthropic, or OpenRouter per config)."""
    provider = get_evaluator_provider()
    model = get_evaluator_model(context_heavy=context_heavy)

    llm: BaseChatModel
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        llm = ChatAnthropic(  # type: ignore[call-arg]
            model_name=model,
            temperature=0,
        )
    elif provider == "openrouter":
        from langchain_openrouter import ChatOpenRouter

        fallbacks = get_llm_model_fallbacks()
        sort = get_openrouter_sort()
        order = get_openrouter_provider_order()
        model_kwargs = {"models": fallbacks} if fallbacks else {}
        provider_prefs: dict[str, object] = {}
        if sort:
            provider_prefs["sort"] = sort
        if order:
            provider_prefs["order"] = order
        openrouter_provider = provider_prefs if provider_prefs else None
        llm = ChatOpenRouter(  # type: ignore[call-arg]
            model=model,
            temperature=0,
            app_url=get_openrouter_app_url(),
            app_title=get_openrouter_app_title(),
            model_kwargs=model_kwargs,
            openrouter_provider=openrouter_provider,
        )
    else:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model=model, temperature=0)

    return llm.with_structured_output(schema, method="json_schema", strict=True)


def _get_page_content(doc: object) -> str:
    """Extract page_content from Document or serialized dict."""
    if isinstance(doc, dict):
        v = doc.get("page_content", "")
        return v if isinstance(v, str) else ""
    v = getattr(doc, "page_content", "")
    return v if isinstance(v, str) else ""


def _documents_to_context(documents: list[Any] | None) -> str:
    """Join document page_content for grader prompts."""
    return "\n\n".join(_get_page_content(d) for d in (documents or []))


# ---------------------------------------------------------------------------
# LLM-as-judge evaluators (2)
# ---------------------------------------------------------------------------


def correctness(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """Compare outputs['answer'] to reference_outputs['answer']."""
    grader = _get_grader_llm(_CorrectnessGrade)
    content = _CORRECTNESS_PROMPT.format(
        question=inputs.get("question", ""),
        reference=reference_outputs.get("answer", ""),
        answer=outputs.get("answer", ""),
    )
    grade = cast(dict[str, Any], grader.invoke([HumanMessage(content=content)]))
    return {"key": "correctness", "score": int(grade["correct"])}


def groundedness(inputs: dict, outputs: dict) -> dict:
    """Compare outputs['answer'] to outputs['documents']."""
    context = _documents_to_context(outputs.get("documents", []))
    grader = _get_grader_llm(_GroundednessGrade, context_heavy=True)
    content = _GROUNDEDNESS_PROMPT.format(
        context=context or "(No retrieved documents)",
        answer=outputs.get("answer", ""),
    )
    grade = cast(dict[str, Any], grader.invoke([HumanMessage(content=content)]))
    return {"key": "groundedness", "score": int(grade["grounded"])}


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
    groundedness,
    has_sources,
    answer_not_empty,
    source_in_expected_docs,
]
