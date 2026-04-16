from __future__ import annotations

import asyncio
import logging
import os
import sys
from textwrap import dedent
from typing import Any

import httpx
import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

API_BASE      = os.environ.get("SPRINGAI_API_URL", "http://localhost:8000")
HTTP_TIMEOUT  = 15.0
DEFAULT_TOP_K = 6

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s  %(name)s  %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("springai-mcp")

server = Server("springai-kb")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_spring_ai",
            description=dedent("""\
                Semantic search over the Spring AI documentation knowledge base.

                Use this when you need to:
                - Understand how to configure or use a Spring AI feature
                - Find code examples (auto-configuration, chat models, embeddings, MCP, etc.)
                - Look up property names, API classes, or integration patterns
                - Understand concepts like RAG, advisors, structured output, tool calling

                Returns ranked chunks with full text including language-tagged code blocks.
                Each result includes its heading_path (e.g. "Ollama Chat > Tool Calling")
                so you know exactly where in the docs it came from.
            """),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Natural language question or keyword query. "
                            "Examples: 'how to configure OllamaChatModel temperature', "
                            "'Spring AI tool calling example', "
                            "'RAG with Chroma vector store'"
                        ),
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default 6, max 20)",
                        "default": DEFAULT_TOP_K,
                        "minimum": 1,
                        "maximum": 20,
                    },
                    "filter_doc": {
                        "type": "string",
                        "description": (
                            "Restrict results to a specific document. "
                            "Use the doc_id from list_topics (e.g. 'ollama-chat', 'tool-calling'). "
                            "Optional."
                        ),
                    },
                    "require_code": {
                        "type": "boolean",
                        "description": "If true, only return chunks that contain code blocks.",
                        "default": False,
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get_document",
            description=dedent("""\
                Fetch the complete contents of a Spring AI documentation page by its doc_id.

                Use this after search_spring_ai identifies a relevant document and you want
                the full page — not just the matched chunk — for complete context.

                Returns all chunks in reading order with full text and code blocks preserved.
            """),
            inputSchema={
                "type": "object",
                "properties": {
                    "doc_id": {
                        "type": "string",
                        "description": (
                            "The document identifier (file stem). "
                            "Obtain from search results or list_topics. "
                            "Examples: 'ollama-chat', 'tool-calling', 'chat-model-api'"
                        ),
                    },
                },
                "required": ["doc_id"],
            },
        ),
        types.Tool(
            name="list_topics",
            description=dedent("""\
                List all Spring AI documentation topics available in the knowledge base.

                Use this to:
                - Discover what's indexed before searching
                - Find the exact doc_id to pass to get_document or filter_doc
                - See which topics have code examples (has_code_chunks > 0)

                Returns each document with its title, category, and chunk counts.
            """),
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter by category (e.g. 'Chat', 'Embeddings'). Optional.",
                    },
                },
                "required": [],
            },
        ),
    ]


async def _call_api(method: str, path: str, **kwargs: Any) -> Any:
    url = f"{API_BASE}{path}"
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        try:
            resp = await (
                client.post(url, **kwargs) if method == "POST" else client.get(url, **kwargs)
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to Spring AI API at {API_BASE}. "
                "Start the server: uvicorn server:app --host 0.0.0.0 --port 8000"
            )
        except httpx.HTTPStatusError as e:
            detail = e.response.json().get("detail", str(e))
            raise RuntimeError(f"API error {e.response.status_code}: {detail}")


def _fmt_search_result(chunk: dict, rank: int) -> str:
    meta_parts = [f"`{chunk['doc_id']}`", chunk["category"]]
    if chunk.get("code_language"):
        meta_parts.append(chunk["code_language"])
    meta_parts.append(chunk.get("chunk_type", "prose"))

    return "\n".join([
        f"### [{rank}] {chunk.get('heading_path') or chunk['title']}",
        f"**Source:** {' · '.join(meta_parts)}  |  **Score:** {chunk['score']:.3f}",
        "",
        chunk["text"],
    ])


def _fmt_doc_chunk(chunk: dict) -> str:
    type_note = chunk.get("chunk_type", "prose")
    if chunk.get("code_language"):
        type_note = f"{type_note} · {chunk['code_language']}"

    return "\n".join([
        f"### {chunk.get('heading_path') or '(top level)'}",
        f"*{type_note}*",
        "",
        chunk["text"],
    ])


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    args = arguments or {}

    try:
        if name == "search_spring_ai":
            query = args.get("query", "").strip()
            if not query:
                return [types.TextContent(type="text", text="Error: query is required")]

            payload: dict[str, Any] = {
                "query": query,
                "top_k": args.get("top_k", DEFAULT_TOP_K),
                "require_code": args.get("require_code", False),
            }
            if args.get("filter_doc"):
                payload["filter_doc"] = args["filter_doc"]

            data = await _call_api("POST", "/search", json=payload)

            if not data["results"]:
                return [types.TextContent(
                    type="text",
                    text=(
                        f"No results found for: '{query}'\n\n"
                        "Try broader terms or use list_topics to discover available docs."
                    ),
                )]

            rerank_note = " · reranked" if data.get("reranked") else ""
            header = (
                f"# Spring AI Docs — Search: {data['query']}\n"
                f"**{data['total_results']} results** · {data['elapsed_ms']:.0f}ms{rerank_note}"
            )
            items: list[types.TextContent] = [types.TextContent(type="text", text=header)]
            for i, chunk in enumerate(data["results"], 1):
                items.append(types.TextContent(type="text", text=_fmt_search_result(chunk, i)))
            return items

        elif name == "get_document":
            doc_id = args.get("doc_id", "").strip()
            if not doc_id:
                return [types.TextContent(type="text", text="Error: doc_id is required")]

            data = await _call_api("GET", f"/docs/{doc_id}")

            header = (
                f"# {data['title']}\n"
                f"**Category:** {data['category']}  |  "
                f"**Doc ID:** `{data['doc_id']}`  |  "
                f"**Chunks:** {data['total_chunks']}"
            )
            items = [types.TextContent(type="text", text=header)]
            for chunk in data["chunks"]:
                items.append(types.TextContent(type="text", text=_fmt_doc_chunk(chunk)))
            return items

        elif name == "list_topics":
            params = {}
            if args.get("category"):
                params["category"] = args["category"]

            data = await _call_api("GET", "/list", params=params)

            if not data:
                return [types.TextContent(
                    type="text",
                    text="No documents indexed yet. Run `python ingest.py`.",
                )]

            lines = [
                "# Spring AI Knowledge Base — Topics\n",
                f"{'Doc ID':<35} {'Title':<40} {'Category':<15} {'Chunks':>6} {'w/Code':>6}",
                "-" * 105,
            ]
            for doc in data:
                lines.append(
                    f"{doc['doc_id']:<35} {doc['title']:<40} {doc['category']:<15} "
                    f"{doc['chunk_count']:>6} {doc['has_code_chunks']:>6}"
                )
            return [types.TextContent(type="text", text="\n".join(lines))]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    except RuntimeError as e:
        return [types.TextContent(type="text", text=f"Error: {e}")]
    except Exception as e:
        log.exception("Unexpected error in tool %s", name)
        return [types.TextContent(type="text", text=f"Unexpected error: {e}")]


async def main() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="springai-kb",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
