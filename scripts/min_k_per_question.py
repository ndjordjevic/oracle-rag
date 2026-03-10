"""Find minimum k per question so each answer is correct.

Runs each question with k=5, 10, 15, ... until the correctness evaluator returns 1.
Reports min k per question and summary.

Usage:
    uv run python scripts/min_k_per_question.py [DATASET_NAME]
    uv run python scripts/min_k_per_question.py                  # default: pinrag-hard-10
    uv run python scripts/min_k_per_question.py pinrag-golden

Requires: LANGSMITH_API_KEY, and OPENAI_API_KEY or ANTHROPIC_API_KEY (for evaluator).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

# Load .env so PINRAG_* and API keys are set
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DEFAULT_DATASET = "pinrag-hard-10"
K_VALUES = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
MAX_K = max(K_VALUES)


def main() -> None:
    dataset_name = (sys.argv[1] if len(sys.argv) > 1 else None) or DEFAULT_DATASET

    if not os.environ.get("LANGSMITH_API_KEY"):
        raise RuntimeError("LANGSMITH_API_KEY not set. Check .env")

    from pinrag.evaluation.evaluators import correctness
    from pinrag.evaluation.target import pinrag_target

    client = Client()
    examples = list(client.list_examples(dataset_name=dataset_name))
    if not examples:
        print(f"No examples in dataset {dataset_name!r}")
        return

    print(f"Dataset: {dataset_name} ({len(examples)} questions)", flush=True)

    # Force no rerank so we're only varying k
    os.environ["PINRAG_USE_RERANK"] = "false"

    results: list[tuple[str, int | None, int]] = []  # (question_short, min_k, tries)

    for i, ex in enumerate(examples):
        question = ex.inputs.get("question", "")
        q_short = question[:70] + ("..." if len(question) > 70 else "")
        min_k: int | None = None
        tries = 0

        for k in K_VALUES:
            os.environ["PINRAG_RETRIEVE_K"] = str(k)
            tries += 1
            result = pinrag_target(ex.inputs)
            grade = correctness(ex.inputs, result, ex.outputs)
            if grade["score"] == 1:
                min_k = k
                break

        results.append((q_short, min_k, tries))
        status = str(min_k) if min_k is not None else f">={MAX_K}"
        print(f"[{i+1}/{len(examples)}] min_k={status} (tries={tries}) | {q_short}", flush=True)

    # Summary
    print()
    print("--- Summary ---")
    for q_short, min_k, tries in results:
        k_str = str(min_k) if min_k is not None else "FAIL"
        print(f"  k={k_str:>3} | {q_short}")

    succeeded = sum(1 for _, k, _ in results if k is not None)
    failed = len(results) - succeeded
    if results:
        avg_k = sum(k for _, k, _ in results if k is not None) / succeeded if succeeded else 0
        print()
        print(f"Questions: {len(results)}, passed: {succeeded}, failed: {failed}")
        if succeeded:
            print(f"Min k (passed): min={min(k for _, k, _ in results if k is not None)}, max={max(k for _, k, _ in results if k is not None)}, avg={avg_k:.1f}")


if __name__ == "__main__":
    main()
