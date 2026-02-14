"""CLI to call the LLM with a test prompt."""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from oracle_rag.llm import get_chat_model


def main() -> None:
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set. Set it in .env or the environment.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Call the OpenAI chat model with a test prompt."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default="Say 'Hello from Oracle RAG' and nothing else.",
        help="Prompt to send (default: simple greeting prompt)",
    )
    args = parser.parse_args()

    llm = get_chat_model()
    response = llm.invoke([HumanMessage(content=args.prompt)])
    print(response.content)


if __name__ == "__main__":
    main()
