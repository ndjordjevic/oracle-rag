"""CLI to run the RAG chain: question over indexed PDFs with answer and citations."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from oracle_rag.embeddings import get_embedding_model
from oracle_rag.llm import get_chat_model
from oracle_rag.rag import run_rag


def main() -> None:
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set. Set it in .env or the environment.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Run RAG: answer a question using indexed PDF chunks, with citations."
    )
    parser.add_argument("query", help="Natural language question")
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Number of chunks to retrieve (default: 5)",
    )
    parser.add_argument(
        "--persist-dir",
        default="chroma_db",
        help="Chroma persistence directory (default: chroma_db)",
    )
    parser.add_argument(
        "--collection",
        default="oracle_rag",
        help="Chroma collection name (default: oracle_rag)",
    )
    args = parser.parse_args()

    persist_dir = Path(args.persist_dir).expanduser().resolve()
    embedding = get_embedding_model()
    llm = get_chat_model()

    result = run_rag(
        args.query,
        llm,
        k=args.k,
        persist_directory=persist_dir,
        collection_name=args.collection,
        embedding=embedding,
    )

    print(result.answer)
    if result.sources:
        print("\nSources:")
        for s in result.sources:
            print(f"  - {s.get('document_id', '?')} (p. {s.get('page', '?')})")


if __name__ == "__main__":
    main()
