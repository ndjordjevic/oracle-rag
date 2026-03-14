"""PinRAG: A PDF RAG system built with LangChain."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pinrag")
except PackageNotFoundError:
    # Fallback for editable/local runs before package metadata is installed.
    __version__ = "0.8.6"
