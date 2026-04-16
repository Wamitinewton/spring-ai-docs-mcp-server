# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A production-ready MCP (Model Context Protocol) server that gives Claude Code semantic search access to Spring AI documentation. It has two runtime components:

1. **`server.py`** — FastAPI retrieval server that owns the FAISS index and embedding model. Must be running before the MCP server can serve queries.
2. **`mcp_server.py`** — MCP stdio server called by Claude Code. It is a thin HTTP client that proxies tool calls to `server.py`.

The `store/` directory (git-ignored) holds the binary FAISS index (`springai.index`) and chunk metadata (`metadata.json`) produced by `ingest.py`. Both files must exist before `server.py` can start.

## Setup & Common Commands

```bash
# Create and activate virtualenv
python3 -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Build the FAISS index (run whenever docs in data/docs/ change)
python ingest.py

# Start the retrieval API (keep running in background)
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Test MCP server directly via stdio
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python mcp_server.py
```

The API URL defaults to `http://localhost:8000`. Override with:
```bash
SPRINGAI_API_URL=http://other-host:8000 python mcp_server.py
```

## Architecture

### Data flow

```
data/docs/*.md  →  ingest.py  →  store/springai.index + metadata.json
                                          ↓
                                      server.py (FastAPI, port 8000)
                                          ↓  HTTP
                                      mcp_server.py (stdio ↔ Claude Code)
```

### Ingestion pipeline (`ingest.py`)

- Reads `.md` files from `data/docs/`, parses YAML-ish frontmatter (`title`, `category`, `source` keys).
- Cleans markdown body while preserving code fences (stash → clean prose → restore).
- Splits into overlapping chunks using a sliding window (400 tokens, 80-token overlap) that never breaks inside a code fence.
- Enriches each chunk with a heading breadcrumb (e.g. `"Ollama Chat > Auto-configuration"`).
- Embeds with `sentence-transformers/all-MiniLM-L6-v2` (384-dim, cosine via inner product on normalized vectors).
- Writes a `faiss.IndexFlatIP` binary and a `metadata.json` array of `Chunk` dicts.

### Retrieval server (`server.py`)

- Loads FAISS index, metadata, and embedding model once at startup into a `_Resources` singleton.
- `POST /search` — embeds the query, runs FAISS search, applies optional `filter_doc` / `require_code` filters, returns ranked `ChunkResult` objects.
- `GET /docs/{doc_id}` — returns all chunks for one document in reading order.
- `GET /list` — aggregates chunk metadata by doc_id for discovery.
- `GET /health` — reports readiness and index stats.

### MCP server (`mcp_server.py`)

Exposes three tools to Claude Code:
- `search_spring_ai` — maps to `POST /search`
- `get_document` — maps to `GET /docs/{doc_id}`
- `list_topics` — maps to `GET /list`

Each tool handler calls `_call_api()` and formats results as markdown text for Claude.

### Doc corpus

31 Spring AI markdown files in `data/docs/`, covering: chat models (Ollama, Azure OpenAI), embeddings, MCP client/server annotations, RAG/ETL pipeline, advisors, tool calling, structured output, multimodality, chat memory, and more. Frontmatter fields used by ingest: `title`, `category`, `source`.
