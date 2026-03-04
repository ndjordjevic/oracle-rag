"""Oracle-RAG evaluation package for LangSmith experiments.

Requires LANGSMITH_API_KEY and OPENAI_API_KEY (for LLM-as-judge grader).
Use the same embedding provider/model as when indexing (see run_evaluation docstring).
By default the collection is oracle_rag_<provider> (e.g. oracle_rag_openai); set ORACLE_RAG_COLLECTION_NAME to override.
See notes/evaluation-strategy.md for full documentation.
"""

from oracle_rag.evaluation.evaluators import EVALUATORS
from oracle_rag.evaluation.run_evaluation import run_baseline
from oracle_rag.evaluation.target import oracle_rag_target

__all__ = [
    "oracle_rag_target",
    "EVALUATORS",
    "run_baseline",
]
