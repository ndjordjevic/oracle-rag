# Embedding Provider Decision

## Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **OpenAI API** | Strong quality, minimal setup, managed | Cost per token, data sent to OpenAI |
| **Hugging Face (local)** | Free, data stays local, no rate limits | GPU/CPU load, model setup |
| **Hugging Face API** | Many models, no local compute | Cost, data sent to HF |
| **Other APIs** (Cohere, Voyage, etc.) | Alternative to OpenAI | Extra integration, vendor lock-in |

## Decision

**We use the OpenAI embedding API** (e.g. `text-embedding-3-small`) for Phase 1.

- Fast to integrate with LangChain (`langchain-openai`).
- Good retrieval quality with no local GPU.
- Can be swapped later via a thin embedding abstraction if we move to local/HF.
