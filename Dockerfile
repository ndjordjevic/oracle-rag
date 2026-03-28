# syntax=docker/dockerfile:1
# OCI image for PinRAG MCP (stdio). Pass API keys at runtime, e.g.:
#   docker run --rm -e OPENAI_API_KEY=... -v pinrag-data:/data/pinrag ghcr.io/ndjordjevic/pinrag:latest

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/ndjordjevic/pinrag"
LABEL org.opencontainers.image.description="PinRAG MCP server (RAG for PDFs, YouTube, GitHub, Discord exports). Optional YouTube vision: build with BUILD_WITH_VISION=1."
LABEL io.modelcontextprotocol.server.name="io.github.ndjordjevic/pinrag"

ARG BUILD_WITH_VISION=0

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PINRAG_PERSIST_DIR=/data/pinrag

RUN useradd --create-home --shell /usr/sbin/nologin --uid 1000 pinrag \
    && mkdir -p /data/pinrag \
    && chown -R pinrag:pinrag /data

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir --upgrade pip \
    && if [ "$BUILD_WITH_VISION" = "1" ]; then \
         apt-get update \
         && apt-get install -y --no-install-recommends ffmpeg \
         && rm -rf /var/lib/apt/lists/* \
         && pip install --no-cache-dir '.[vision]'; \
       else \
         pip install --no-cache-dir .; \
       fi

USER pinrag
WORKDIR /home/pinrag

VOLUME ["/data/pinrag"]

CMD ["pinrag"]
