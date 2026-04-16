"""
server.py — Spring AI MCP Knowledge Base — FastAPI Retrieval Server v2

Changes from v1:
  - BGE query instruction prefix on all query embeddings (matches ingest.py)
  - Cross-encoder reranking (ms-marco-MiniLM-L-6-v2) applied after FAISS retrieval
  - Manifest-driven config: model name / dim / instructions read from store/manifest.json
  - Richer ChunkResult: chunk_type, code_language, heading_hierarchy, quality_score
  - /search accepts rerank=true (default) and rerank_top_k for two-stage retrieval
  - IVFFlat nprobe tuned at startup for recall/speed balance

Run with:
    uvicorn server:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── paths ─────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).parent
INDEX_PATH    = ROOT / "store" / "springai.index"
META_PATH     = ROOT / "store" / "metadata.json"
MANIFEST_PATH = ROOT / "store" / "manifest.json"

# Reranker — lightweight cross-encoder, fast enough for top-40 candidates
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

DEFAULT_TOP_K  = 6
MAX_TOP_K      = 20
# Retrieve this many candidates from FAISS before reranking
RETRIEVAL_MULT = 5   # fetch top_k * RETRIEVAL_MULT, rerank, return top_k

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("springai-mcp")


# ═══════════════════════════════════════════════════════════════════════════
# Resource singleton
# ═══════════════════════════════════════════════════════════════════════════

class Resources:
    """
    Loaded once at startup. Holds:
      - FAISS index
      - metadata list
      - bi-encoder (SentenceTransformer for query embedding)
      - cross-encoder (for reranking)
      - manifest (config dict)
    """

    def __init__(self) -> None:
        import faiss
        from sentence_transformers import SentenceTransformer, CrossEncoder

        for path in (INDEX_PATH, META_PATH, MANIFEST_PATH):
            if not path.exists():
                raise RuntimeError(
                    f"{path.name} not found. Run `python ingest.py` first."
                )

        # ── manifest ──
        self.manifest: dict = json.loads(MANIFEST_PATH.read_text())
        self.embed_model_name: str   = self.manifest["embed_model"]
        self.embed_dim: int          = self.manifest["embed_dim"]
        self.query_instruction: str  = self.manifest.get("query_instruction", "")
        log.info("Manifest loaded: model=%s dim=%d", self.embed_model_name, self.embed_dim)

        # ── FAISS index ──
        log.info("Loading FAISS index from %s", INDEX_PATH)
        self.index = faiss.read_index(str(INDEX_PATH))
        log.info("Index: %d vectors (%s)", self.index.ntotal, self.manifest.get("index_type", "?"))

        # Tune IVFFlat nprobe for higher recall (sqrt of n_lists, min 8)
        if hasattr(self.index, "nprobe"):
            n_lists = getattr(self.index, "nlist", 1)
            self.index.nprobe = max(8, int(n_lists ** 0.5))
            log.info("IVFFlat nprobe set to %d", self.index.nprobe)

        # ── metadata ──
        log.info("Loading metadata from %s", META_PATH)
        self.metadata: list[dict] = json.loads(META_PATH.read_text())
        log.info("Loaded %d chunk records", len(self.metadata))

        # ── bi-encoder ──
        log.info("Loading bi-encoder: %s", self.embed_model_name)
        self.bi_encoder = SentenceTransformer(self.embed_model_name)
        log.info("Bi-encoder ready")

        # ── cross-encoder (reranker) ──
        log.info("Loading cross-encoder reranker: %s", RERANKER_MODEL)
        self.cross_encoder = CrossEncoder(RERANKER_MODEL)
        log.info("Cross-encoder ready")

    # ── query embedding ────────────────────────────────────────────────────

    def embed_query(self, query: str) -> np.ndarray:
        """
        BGE expects the query instruction prefix to be prepended.
        This must match how ingest.py embedded documents.
        """
        prefixed = f"{self.query_instruction}\n{query}" if self.query_instruction else query
        vec = self.bi_encoder.encode(
            [prefixed],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return vec.astype("float32")

    # ── two-stage retrieval ────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        filter_doc: str | None = None,
        require_code: bool = False,
        rerank: bool = True,
    ) -> list[dict]:
        """
        Stage 1 — FAISS ANN search (bi-encoder).
        Stage 2 — Cross-encoder reranking of candidates.
        """
        # Over-fetch so we have candidates to rerank even after filtering
        fetch_k = min(top_k * RETRIEVAL_MULT, len(self.metadata))
        vec = self.embed_query(query)
        scores, indices = self.index.search(vec, fetch_k)

        candidates: list[dict] = []
        for bi_score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            chunk = dict(self.metadata[idx])
            chunk["bi_encoder_score"] = float(bi_score)
            chunk["chunk_id_int"] = int(idx)
            candidates.append(chunk)

        # ── filters ──
        if filter_doc:
            candidates = [c for c in candidates if c["doc_id"] == filter_doc]
        if require_code:
            candidates = [c for c in candidates if c["has_code"]]

        if not candidates:
            return []

        # ── cross-encoder reranking ──
        if rerank:
            pairs = [(query, c["text"]) for c in candidates]
            rerank_scores = self.cross_encoder.predict(pairs)
            for chunk, rs in zip(candidates, rerank_scores):
                chunk["score"] = float(rs)
            candidates.sort(key=lambda c: c["score"], reverse=True)
        else:
            for chunk in candidates:
                chunk["score"] = chunk["bi_encoder_score"]

        return candidates[:top_k]


_resources: Resources | None = None


def get_resources() -> Resources:
    global _resources
    if _resources is None:
        _resources = Resources()
    return _resources


# ═══════════════════════════════════════════════════════════════════════════
# FastAPI app
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Spring AI MCP Knowledge Base v2",
    description="Semantic search + cross-encoder reranking over Spring AI docs",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    try:
        get_resources()
        log.info("All resources loaded and ready.")
    except RuntimeError as e:
        log.error("Startup failed: %s", e)


# ═══════════════════════════════════════════════════════════════════════════
# Request / Response models
# ═══════════════════════════════════════════════════════════════════════════

class SearchRequest(BaseModel):
    query:       str       = Field(..., min_length=1, max_length=500)
    top_k:       int       = Field(DEFAULT_TOP_K, ge=1, le=MAX_TOP_K)
    filter_doc:  str | None = Field(None, description="Restrict to a specific doc_id")
    require_code: bool     = Field(False, description="Only return chunks with code")
    rerank:      bool      = Field(True,  description="Apply cross-encoder reranking")


class ChunkResult(BaseModel):
    # identity
    chunk_id:     str
    doc_id:       str
    chunk_index:  int
    # provenance
    title:        str
    category:     str
    source:       str
    heading_path: str
    heading_hierarchy: list[str]
    # content
    chunk_type:   str
    text:         str
    has_code:     bool
    code_language: str
    # scores
    token_count:  int
    quality_score: float
    score:        float          # final ranking score (reranker if enabled)
    bi_encoder_score: float      # raw FAISS cosine similarity


class SearchResponse(BaseModel):
    query:         str
    total_results: int
    reranked:      bool
    results:       list[ChunkResult]
    elapsed_ms:    float


class HealthResponse(BaseModel):
    status:          str
    embed_model:     str | None
    reranker_model:  str
    index_vectors:   int | None
    metadata_chunks: int | None
    index_type:      str | None


class DocumentResponse(BaseModel):
    doc_id:       str
    title:        str
    category:     str
    total_chunks: int
    chunks:       list[dict[str, Any]]


class ListItem(BaseModel):
    doc_id:         str
    title:          str
    category:       str
    chunk_count:    int
    has_code_chunks: int
    avg_quality:    float


# ═══════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search(req: SearchRequest) -> SearchResponse:
    """
    Two-stage retrieval:
      1. FAISS bi-encoder ANN search (over-fetches by 5×)
      2. Cross-encoder reranking of candidates (unless rerank=false)

    Scores in results are cross-encoder logits when reranked,
    or cosine similarity when rerank=false.
    """
    t0 = time.perf_counter()
    try:
        res = get_resources()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    results = res.search(
        query=req.query,
        top_k=req.top_k,
        filter_doc=req.filter_doc,
        require_code=req.require_code,
        rerank=req.rerank,
    )

    elapsed = (time.perf_counter() - t0) * 1000

    # Fill in any missing v2 fields from older metadata gracefully
    chunk_results = []
    for r in results:
        chunk_results.append(ChunkResult(
            chunk_id=r.get("chunk_id", ""),
            doc_id=r["doc_id"],
            chunk_index=r["chunk_index"],
            title=r["title"],
            category=r["category"],
            source=r["source"],
            heading_path=r.get("heading_path", ""),
            heading_hierarchy=r.get("heading_hierarchy", []),
            chunk_type=r.get("chunk_type", "prose"),
            text=r["text"],
            has_code=r["has_code"],
            code_language=r.get("code_language", ""),
            token_count=r.get("token_count", 0),
            quality_score=r.get("quality_score", 0.0),
            score=r["score"],
            bi_encoder_score=r.get("bi_encoder_score", r["score"]),
        ))

    return SearchResponse(
        query=req.query,
        total_results=len(chunk_results),
        reranked=req.rerank,
        results=chunk_results,
        elapsed_ms=round(elapsed, 2),
    )


@app.get("/health", response_model=HealthResponse, tags=["Meta"])
async def health() -> HealthResponse:
    try:
        res = get_resources()
        return HealthResponse(
            status="ready",
            embed_model=res.embed_model_name,
            reranker_model=RERANKER_MODEL,
            index_vectors=res.index.ntotal,
            metadata_chunks=len(res.metadata),
            index_type=res.manifest.get("index_type"),
        )
    except RuntimeError:
        return HealthResponse(
            status="not_ready — run python ingest.py first",
            embed_model=None,
            reranker_model=RERANKER_MODEL,
            index_vectors=None,
            metadata_chunks=None,
            index_type=None,
        )


@app.get("/docs/{doc_id}", response_model=DocumentResponse, tags=["Documents"])
async def get_document(doc_id: str) -> DocumentResponse:
    """Fetch all chunks for a document, in reading order."""
    try:
        res = get_resources()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    doc_chunks = sorted(
        [m for m in res.metadata if m["doc_id"] == doc_id],
        key=lambda c: c["chunk_index"],
    )
    if not doc_chunks:
        raise HTTPException(status_code=404, detail=f"No document with doc_id='{doc_id}'")

    return DocumentResponse(
        doc_id=doc_id,
        title=doc_chunks[0]["title"],
        category=doc_chunks[0]["category"],
        total_chunks=len(doc_chunks),
        chunks=doc_chunks,
    )


@app.get("/list", response_model=list[ListItem], tags=["Documents"])
async def list_documents(
    category: str | None = Query(None, description="Filter by category"),
) -> list[ListItem]:
    """List all indexed documents with chunk counts and average quality."""
    try:
        res = get_resources()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    docs: dict[str, dict] = {}
    for chunk in res.metadata:
        did = chunk["doc_id"]
        if did not in docs:
            docs[did] = {
                "doc_id": did,
                "title": chunk["title"],
                "category": chunk["category"],
                "chunk_count": 0,
                "has_code_chunks": 0,
                "quality_sum": 0.0,
            }
        docs[did]["chunk_count"] += 1
        if chunk["has_code"]:
            docs[did]["has_code_chunks"] += 1
        docs[did]["quality_sum"] += chunk.get("quality_score", 0.5)

    result = [
        ListItem(
            doc_id=d["doc_id"],
            title=d["title"],
            category=d["category"],
            chunk_count=d["chunk_count"],
            has_code_chunks=d["has_code_chunks"],
            avg_quality=round(d["quality_sum"] / max(d["chunk_count"], 1), 3),
        )
        for d in docs.values()
    ]

    if category:
        result = [d for d in result if d.category.lower() == category.lower()]

    return sorted(result, key=lambda d: d.title)


@app.get("/manifest", tags=["Meta"])
async def get_manifest() -> dict:
    """Return the ingestion manifest (model config, chunk stats, timestamp)."""
    try:
        res = get_resources()
        return res.manifest
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))