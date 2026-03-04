"""Run oracle-rag baseline evaluation via LangSmith.

Usage:
    uv run python -m oracle_rag.evaluation
    uv run python -m oracle_rag.evaluation --dataset oracle-rag-golden --prefix oracle-rag-baseline
    uv run python -m oracle_rag.evaluation --limit 30
    uv run python -m oracle_rag.evaluation --metadata '{"version":"3.0.1"}'

Requires: LANGSMITH_API_KEY, OPENAI_API_KEY (for LLM-as-judge grader).

Embedding: Use the same ORACLE_RAG_EMBEDDING_PROVIDER / ORACLE_RAG_EMBEDDING_MODEL
(as in .env) that was used when indexing the Chroma collection. A dimension mismatch
(e.g. "expecting 1536, got 1024") means the index was built with a different model.

Collection: By default the retriever uses oracle_rag_<provider> (e.g. oracle_rag_openai).
Set ORACLE_RAG_COLLECTION_NAME to override (e.g. oracle_rag for a single shared collection).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

from oracle_rag.evaluation.evaluators import EVALUATORS
from oracle_rag.evaluation.target import oracle_rag_target


def _load_env() -> None:
    """Load .env from cwd or project root."""
    cwd = Path.cwd()
    for path in (cwd / ".env", cwd.parent / ".env"):
        if path.exists():
            load_dotenv(path)
            return
    load_dotenv()


def _check_env() -> None:
    """Require LANGSMITH_API_KEY and OPENAI_API_KEY."""
    missing = []
    if not os.environ.get("LANGSMITH_API_KEY"):
        missing.append("LANGSMITH_API_KEY")
    if not os.environ.get("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY")
    if missing:
        print(
            f"Error: Missing required env vars: {', '.join(missing)}. "
            "Set them in .env or the environment.",
            file=sys.stderr,
        )
        sys.exit(1)


def run_baseline(
    *,
    dataset: str = "oracle-rag-golden",
    experiment_prefix: str = "oracle-rag-baseline",
    metadata: dict | None = None,
    limit: int | None = None,
) -> None:
    """Run baseline evaluation via LangSmith client.evaluate().

    When limit is set, loads that many examples explicitly so all are evaluated
    (e.g. limit=30 for the full oracle-rag-golden set). Otherwise passes the
    dataset name and LangSmith uses all examples.
    """
    _load_env()
    _check_env()

    client = Client()
    metadata = metadata or {}

    if limit is not None:
        data = list(client.list_examples(dataset_name=dataset, limit=limit))
        print(f"Loaded {len(data)} examples from dataset {dataset!r} (limit={limit}).")
    else:
        data = dataset

    results = client.evaluate(
        oracle_rag_target,
        data=data,
        evaluators=EVALUATORS,
        experiment_prefix=experiment_prefix,
        metadata=metadata,
    )

    name = getattr(results, "experiment_name", None) or "experiment"
    print(f"\nEvaluation complete. Experiment: {name}")
    print("View results at https://smith.langchain.com/")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run oracle-rag baseline evaluation via LangSmith."
    )
    parser.add_argument(
        "--dataset",
        default="oracle-rag-golden",
        help="Dataset name (default: oracle-rag-golden)",
    )
    parser.add_argument(
        "--prefix",
        default="oracle-rag-baseline",
        dest="experiment_prefix",
        help="Experiment name prefix (default: oracle-rag-baseline)",
    )
    parser.add_argument(
        "--metadata",
        default=None,
        help="Optional JSON metadata, e.g. '{\"version\":\"3.0.1\"}'",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Max number of dataset examples to evaluate (default: all). Use e.g. 30 for full oracle-rag-golden.",
    )
    args = parser.parse_args()

    metadata = None
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid --metadata JSON: {e}", file=sys.stderr)
            sys.exit(1)

    run_baseline(
        dataset=args.dataset,
        experiment_prefix=args.experiment_prefix,
        metadata=metadata,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
