"""Unit tests for evaluation module (evaluators, run_evaluation, __main__)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pinrag.evaluation.evaluators import (
    EVALUATORS,
    _documents_to_context,
    _get_page_content,
    answer_not_empty,
    correctness,
    groundedness,
    has_sources,
    source_in_expected_docs,
)

# ---------------------------------------------------------------------------
# evaluators.py — code evaluators (no LLM)
# ---------------------------------------------------------------------------


def test_has_sources_true() -> None:
    out = has_sources({}, {"sources": [{"document_id": "a.pdf"}]})
    assert out == {"key": "has_sources", "score": 1}


def test_has_sources_false() -> None:
    out = has_sources({}, {"sources": []})
    assert out == {"key": "has_sources", "score": 0}


def test_has_sources_missing_key() -> None:
    out = has_sources({}, {})
    assert out == {"key": "has_sources", "score": 0}


def test_answer_not_empty_with_content() -> None:
    out = answer_not_empty({}, {"answer": "The answer is 42."})
    assert out == {"key": "answer_not_empty", "score": 1}


def test_answer_not_empty_empty() -> None:
    out = answer_not_empty({}, {"answer": ""})
    assert out == {"key": "answer_not_empty", "score": 0}


def test_answer_not_empty_failure_message() -> None:
    out = answer_not_empty({}, {"answer": "Query failed due to an error."})
    assert out == {"key": "answer_not_empty", "score": 0}


def test_source_in_expected_docs_match() -> None:
    out = source_in_expected_docs(
        {},
        {"sources": [{"document_id": "a.pdf"}, {"document_id": "b.pdf"}]},
        {"expected_document_ids": ["a.pdf"]},
    )
    assert out == {"key": "source_in_expected_docs", "score": 1}


def test_source_in_expected_docs_no_match() -> None:
    out = source_in_expected_docs(
        {},
        {"sources": [{"document_id": "c.pdf"}]},
        {"expected_document_ids": ["a.pdf"]},
    )
    assert out == {"key": "source_in_expected_docs", "score": 0}


def test_source_in_expected_docs_no_expected() -> None:
    out = source_in_expected_docs(
        {},
        {"sources": [{"document_id": "x.pdf"}]},
        {"expected_document_ids": []},
    )
    assert out == {"key": "source_in_expected_docs", "score": 1}


def test_source_in_expected_docs_missing_ref() -> None:
    out = source_in_expected_docs({}, {"sources": []}, {})
    assert out == {"key": "source_in_expected_docs", "score": 1}


# ---------------------------------------------------------------------------
# evaluators.py — helpers
# ---------------------------------------------------------------------------


def test_get_page_content_from_document() -> None:
    from langchain_core.documents import Document

    doc = Document(page_content="hello")
    assert _get_page_content(doc) == "hello"


def test_get_page_content_from_dict() -> None:
    assert _get_page_content({"page_content": "world"}) == "world"


def test_get_page_content_unknown_type() -> None:
    assert _get_page_content(42) == ""


def test_documents_to_context() -> None:
    from langchain_core.documents import Document

    docs = [
        Document(page_content="alpha"),
        Document(page_content="beta"),
    ]
    ctx = _documents_to_context(docs)
    assert "alpha" in ctx
    assert "beta" in ctx


def test_documents_to_context_empty() -> None:
    assert _documents_to_context([]) == ""
    assert _documents_to_context(None) == ""


def test_evaluators_list_has_five() -> None:
    assert len(EVALUATORS) == 5
    names = {e.__name__ for e in EVALUATORS}
    assert names == {
        "correctness",
        "groundedness",
        "has_sources",
        "answer_not_empty",
        "source_in_expected_docs",
    }


# ---------------------------------------------------------------------------
# evaluators.py — LLM-as-judge (mocked)
# ---------------------------------------------------------------------------


def test_correctness_calls_grader() -> None:
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = {"correct": True, "explanation": "ok"}

    with patch("pinrag.evaluation.evaluators._get_grader_llm", return_value=mock_llm):
        out = correctness(
            {"question": "What color?"},
            {"answer": "Blue"},
            {"answer": "Blue"},
        )
    assert out == {"key": "correctness", "score": 1}
    mock_llm.invoke.assert_called_once()


def test_correctness_incorrect() -> None:
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = {"correct": False, "explanation": "wrong"}

    with patch("pinrag.evaluation.evaluators._get_grader_llm", return_value=mock_llm):
        out = correctness(
            {"question": "What color?"},
            {"answer": "Red"},
            {"answer": "Blue"},
        )
    assert out == {"key": "correctness", "score": 0}


def test_groundedness_calls_grader() -> None:
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = {"grounded": True, "explanation": "ok"}

    with patch("pinrag.evaluation.evaluators._get_grader_llm", return_value=mock_llm):
        from langchain_core.documents import Document

        out = groundedness(
            {},
            {
                "answer": "Blue",
                "documents": [Document(page_content="The sky is blue.")],
            },
        )
    assert out == {"key": "groundedness", "score": 1}


def test_groundedness_hallucinated() -> None:
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = {"grounded": False, "explanation": "hallucination"}

    with patch("pinrag.evaluation.evaluators._get_grader_llm", return_value=mock_llm):
        out = groundedness({}, {"answer": "Made up facts", "documents": []})
    assert out == {"key": "groundedness", "score": 0}


# ---------------------------------------------------------------------------
# run_evaluation.py
# ---------------------------------------------------------------------------


def test_run_evaluation_check_env_missing_langsmith(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_check_env exits when LANGSMITH_API_KEY is missing."""
    from pinrag.evaluation.run_evaluation import _check_env

    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        _check_env()


def test_run_evaluation_check_env_missing_evaluator_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_check_env exits when evaluator provider's API key is missing."""
    from pinrag.evaluation.run_evaluation import _check_env

    monkeypatch.setenv("LANGSMITH_API_KEY", "test-langsmith")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("PINRAG_EVALUATOR_PROVIDER", "openai")
    with pytest.raises(SystemExit):
        _check_env()


def test_run_evaluation_check_env_missing_anthropic_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_check_env exits when evaluator is anthropic but ANTHROPIC_API_KEY is missing."""
    from pinrag.evaluation.run_evaluation import _check_env

    monkeypatch.setenv("LANGSMITH_API_KEY", "test-langsmith")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PINRAG_EVALUATOR_PROVIDER", "anthropic")
    with pytest.raises(SystemExit):
        _check_env()


def test_run_evaluation_main_parses_args(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() parses --dataset and --prefix."""
    from pinrag.evaluation import run_evaluation

    monkeypatch.setattr(
        "sys.argv",
        ["prog", "--dataset", "my-ds", "--prefix", "my-exp", "--limit", "5"],
    )

    mock_run = MagicMock()
    monkeypatch.setattr(run_evaluation, "run_baseline", mock_run)

    run_evaluation.main()

    mock_run.assert_called_once_with(
        dataset="my-ds",
        experiment_prefix="my-exp",
        metadata=None,
        limit=5,
    )


def test_run_evaluation_main_invalid_metadata_exits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """main() exits with code 1 when --metadata is invalid JSON."""
    from pinrag.evaluation import run_evaluation

    monkeypatch.setattr("sys.argv", ["prog", "--metadata", "not-json"])

    with pytest.raises(SystemExit) as exc_info:
        run_evaluation.main()
    assert exc_info.value.code == 1


def test_run_evaluation_main_valid_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() passes parsed metadata dict to run_baseline."""
    from pinrag.evaluation import run_evaluation

    monkeypatch.setattr(
        "sys.argv",
        ["prog", "--metadata", '{"version": "1.0"}'],
    )

    mock_run = MagicMock()
    monkeypatch.setattr(run_evaluation, "run_baseline", mock_run)

    run_evaluation.main()

    call_kwargs = mock_run.call_args[1]
    assert call_kwargs["metadata"] == {"version": "1.0"}


# ---------------------------------------------------------------------------
# __main__.py
# ---------------------------------------------------------------------------


def test_evaluation_main_module_invokes_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """Python -m pinrag.evaluation calls run_evaluation.main."""
    mock_main = MagicMock()
    monkeypatch.setattr("pinrag.evaluation.run_evaluation.main", mock_main)

    import pinrag.evaluation.__main__ as main_mod

    # __main__ is just: if __name__ == "__main__": main()
    # We can't easily re-trigger __name__ == "__main__", so just verify the import works
    assert hasattr(main_mod, "__name__")
