# Embedding Provider Decision

## Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **OpenAI API** | Strong quality, minimal setup, managed | Cost per token, data sent to OpenAI |
| **Hugging Face (local)** | Free, data stays local, no rate limits | GPU/CPU load, model setup |
| **Hugging Face API** | Many models, no local compute | Cost, data sent to HF |
| **Other APIs** (Cohere, Voyage, etc.) | Alternative to OpenAI | Extra integration, vendor lock-in |

## Decision (historical)

Phase 1 originally used the **OpenAI embedding API** (e.g. `text-embedding-3-small`).

## Current (supersedes above)

**Embeddings are local-only:** `nomic-embed-text-v1.5` via `langchain-nomic` (`NomicEmbeddings`, `inference_mode="local"`). No embedding API key; weights download once (~270 MB). **Existing Chroma indexes built with OpenAI 1536-dim vectors are incompatible** — use a new persist dir / collection and re-index.

The LLM path may still use OpenAI (`OPENAI_API_KEY`) or Anthropic; that is separate from embeddings.
