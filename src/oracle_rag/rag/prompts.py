"""Prompt templates for the RAG chain."""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

RAG_SYSTEM = """You are a helpful assistant that answers questions based only on the provided context from PDF documents.
If the context does not contain enough information to answer the question, say so.
You may cite sources using the labels [1], [2], etc. that appear next to each context block."""

RAG_HUMAN = """Context:
{context}

Question: {question}"""

# Prompt with context and question placeholders for the RAG chain.
RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", RAG_SYSTEM),
        ("human", RAG_HUMAN),
    ]
)
