"""PinRAG evaluation package for LangSmith experiments.

Requires LANGSMITH_API_KEY and an API key for the judge LLM (``OPENAI_API_KEY`` or
``ANTHROPIC_API_KEY`` per ``PINRAG_EVALUATOR_PROVIDER``). Use the same embedding
provider/model as when indexing (see ``run_evaluation`` module docstring). By default
the collection is ``pinrag_<provider>`` (e.g. ``pinrag_openai``); set
``PINRAG_COLLECTION_NAME`` to override. See ``notes/evaluation-strategy.md`` for full
documentation.
"""

from pinrag.evaluation.evaluators import EVALUATORS
from pinrag.evaluation.run_evaluation import run_baseline
from pinrag.evaluation.target import pinrag_target

__all__ = [
    "pinrag_target",
    "EVALUATORS",
    "run_baseline",
]
