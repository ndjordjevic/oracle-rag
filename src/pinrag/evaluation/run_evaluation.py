"""Run pinrag baseline evaluation via LangSmith.

Usage:
    uv run python -m pinrag.evaluation
    uv run python -m pinrag.evaluation --dataset pinrag-golden --prefix pinrag-baseline
    uv run python -m pinrag.evaluation --limit 30
    uv run python -m pinrag.evaluation --metadata '{"version":"3.0.1"}'

Requires: LANGSMITH_API_KEY; OPENAI_API_KEY or ANTHROPIC_API_KEY (per PINRAG_EVALUATOR_PROVIDER).

Embedding: Use the same PINRAG_EMBEDDING_PROVIDER / PINRAG_EMBEDDING_MODEL
(as in .env) that was used when indexing the Chroma collection. A dimension mismatch
(e.g. "expecting 1536, got 1024") means the index was built with a different model.

Collection: By default the retriever uses pinrag_<provider> (e.g. pinrag_openai).
Set PINRAG_COLLECTION_NAME to override (e.g. pinrag for a single shared collection).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

from pinrag.evaluation.evaluators import EVALUATORS
from pinrag.evaluation.target import pinrag_target


def _load_env() -> None:
    """Load .env from cwd or project root."""
    cwd = Path.cwd()
    for path in (cwd / ".env", cwd.parent / ".env"):
        if path.exists():
            load_dotenv(path)
            return
    load_dotenv()


def _check_env() -> None:
    """Require LANGSMITH_API_KEY and API key for evaluator provider (OPENAI or ANTHROPIC)."""
    from pinrag.config import get_evaluator_provider

    missing = []
    if not os.environ.get("LANGSMITH_API_KEY"):
        missing.append("LANGSMITH_API_KEY")
    provider = get_evaluator_provider()
    if provider == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    elif provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
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
    dataset: str = "pinrag-golden",
    experiment_prefix: str = "pinrag-baseline",
    metadata: dict | None = None,
    limit: int | None = None,
) -> None:
    """Run baseline evaluation via LangSmith client.evaluate().

    When limit is set, loads that many examples explicitly so all are evaluated
    (e.g. limit=30 for the full pinrag-golden set). Otherwise passes the
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
        pinrag_target,
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
        description="Run pinrag baseline evaluation via LangSmith."
    )
    parser.add_argument(
        "--dataset",
        default="pinrag-golden",
        help="Dataset name (default: pinrag-golden)",
    )
    parser.add_argument(
        "--prefix",
        default="pinrag-baseline",
        dest="experiment_prefix",
        help="Experiment name prefix (default: pinrag-baseline)",
    )
    parser.add_argument(
        "--metadata",
        default=None,
        help='Optional JSON metadata, e.g. \'{"version":"3.0.1"}\'',
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Max number of dataset examples to evaluate (default: all). Use e.g. 30 for full pinrag-golden.",
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
