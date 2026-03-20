"""CLI to call the LLM with a test prompt."""

from __future__ import annotations

import argparse
import sys

import _script_env

from langchain_core.messages import HumanMessage  # noqa: E402

from pinrag.llm import get_chat_model  # noqa: E402


def main() -> None:
    err = _script_env.llm_keys_error_message()
    if err:
        print(err, file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Call the configured chat model (PINRAG_LLM_PROVIDER) with a test prompt."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default="Say 'Hello from PinRAG' and nothing else.",
        help="Prompt to send (default: simple greeting prompt)",
    )
    args = parser.parse_args()

    llm = get_chat_model()
    response = llm.invoke([HumanMessage(content=args.prompt)])
    print(response.content)


if __name__ == "__main__":
    main()
