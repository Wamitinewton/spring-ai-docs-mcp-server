from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress, SpinnerColumn, TextColumn,
    BarColumn, TaskProgressColumn, TimeElapsedColumn,
)
from rich.table import Table
from rich import box

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("springai-ingest")
console = Console()

EMBED_MODEL        = "BAAI/bge-large-en-v1.5"
EMBED_DIM          = 1024
DOC_INSTRUCTION    = "Represent this document for retrieval: "
QUERY_INSTRUCTION  = "Represent this question for searching relevant passages: "
MAX_CHUNK_TOKENS   = 350
OVERLAP_TOKENS     = 60
MIN_CHUNK_TOKENS   = 25
MIN_QUALITY_SCORE  = 0.30
CODE_CONTEXT_SENTS = 2

_FRONTMATTER_RE    = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
_HEADING_RE        = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_CODE_FENCE_RE     = re.compile(r"```(\w*)\n([\s\S]*?)```", re.MULTILINE)
_INLINE_CODE_RE    = re.compile(r"`[^`\n]+`")
_TABLE_SEP_RE      = re.compile(r"^\|[-:| ]+\|$", re.MULTILINE)
_TABLE_ROW_RE      = re.compile(r"^\|.+\|$", re.MULTILINE)
_PROP_NOISE_RE     = re.compile(r"^(Property|Description|Default|Type)\s*$", re.MULTILINE)
_BLANK_LINES_RE    = re.compile(r"\n{3,}")
_NAV_LINK_RE       = re.compile(r"^\[.{1,60}\]\(#.+\)$", re.MULTILINE)
_ADMONITION_RE     = re.compile(r"^(NOTE|TIP|WARNING|IMPORTANT|CAUTION)$", re.MULTILINE)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    chunk_id:          str
    doc_id:            str
    chunk_index:       int
    title:             str
    category:          str
    source:            str
    heading_path:      str
    heading_hierarchy: list[str]
    chunk_type:        str
    text:              str
    has_code:          bool
    code_language:     str
    token_count:       int
    quality_score:     float


@dataclass
class Section:
    level:      int
    heading:    str
    ancestors:  list[str]
    body:       str
    char_start: int


@dataclass
class Segment:
    kind:     str
    text:     str
    language: str = ""


def _make_chunk_id(doc_id: str, text: str) -> str:
    return hashlib.md5(f"{doc_id}:{text}".encode()).hexdigest()[:16]


def _approx_tokens(text: str) -> int:
    return len(text.split())


def _primary_language(text: str) -> str:
    langs = re.findall(r"```(\w+)", text)
    if not langs:
        return ""
    priority = {"java", "kotlin", "xml", "yaml", "json", "groovy", "properties"}
    for lang in langs:
        if lang.lower() in priority:
            return lang.lower()
    return langs[0].lower()


def _last_n_sentences(text: str, n: int) -> str:
    parts = _SENTENCE_SPLIT_RE.split(text.strip())
    return " ".join(parts[-n:]).strip()


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    meta: dict = {}
    m = _FRONTMATTER_RE.match(raw)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip().strip('"')
        raw = raw[m.end():]
    return meta, raw


def clean_prose(text: str) -> str:
    text = _TABLE_SEP_RE.sub("", text)
    text = _PROP_NOISE_RE.sub("", text)
    text = _NAV_LINK_RE.sub("", text)
    text = _ADMONITION_RE.sub("", text)
    text = _INLINE_CODE_RE.sub(lambda m: m.group(0)[1:-1], text)
    text = _BLANK_LINES_RE.sub("\n\n", text)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


def split_into_sections(body: str) -> list[Section]:
    headings = [
        (m.start(), len(m.group(1)), m.group(2).strip())
        for m in _HEADING_RE.finditer(body)
    ]

    if not headings:
        return [Section(level=1, heading="", ancestors=[], body=body, char_start=0)]

    sections: list[Section] = []
    active: dict[int, str] = {}

    for i, (pos, level, heading_text) in enumerate(headings):
        next_pos = headings[i + 1][0] if i + 1 < len(headings) else len(body)
        section_body = body[pos:next_pos]
        newline_pos = section_body.find("\n")
        section_body = section_body[newline_pos + 1:] if newline_pos != -1 else ""

        for lvl in list(active.keys()):
            if lvl >= level:
                del active[lvl]
        active[level] = heading_text

        ancestors = [active[k] for k in sorted(active.keys()) if k < level]

        sections.append(Section(
            level=level,
            heading=heading_text,
            ancestors=ancestors,
            body=section_body.strip(),
            char_start=pos,
        ))

    return sections


def section_to_segments(body: str) -> list[Segment]:
    segments: list[Segment] = []
    last_end = 0

    for m in _CODE_FENCE_RE.finditer(body):
        prose_before = body[last_end:m.start()]
        for para in prose_before.split("\n\n"):
            para = para.strip()
            if para:
                segments.append(Segment(kind="prose", text=para))

        lang = m.group(1).strip().lower() or "text"
        segments.append(Segment(kind="code", text=m.group(2), language=lang))
        last_end = m.end()

    for para in body[last_end:].split("\n\n"):
        para = para.strip()
        if para:
            segments.append(Segment(kind="prose", text=para))

    return segments


def _quality_score(text: str, has_code: bool) -> float:
    words = text.split()
    if not words:
        return 0.0
    total = len(words)
    noise_ratio = min(
        (len(_PROP_NOISE_RE.findall(text)) * 3
         + len(_TABLE_ROW_RE.findall(text))
         + len(_NAV_LINK_RE.findall(text)) * 2) / max(total, 1),
        1.0,
    )
    tech_ratio = min(
        sum(1 for w in words if "." in w or "_" in w or (w[0].isupper() and len(w) > 4))
        / max(total, 1),
        1.0,
    )
    return round(
        min(max((1 - noise_ratio) * 0.5 + tech_ratio * 0.35 + (0.15 if has_code else 0.0), 0.0), 1.0),
        3,
    )


def _build_chunks_from_segments(
    segments: list[Segment],
    heading_path: str,
    heading_hierarchy: list[str],
    doc_id: str,
    title: str,
    category: str,
    source: str,
    start_index: int,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    chunk_index = start_index
    buf: list[str] = []
    buf_tokens = 0
    last_prose = ""

    def emit(text: str, ctype: str, clang: str = "") -> None:
        nonlocal chunk_index
        wc = _approx_tokens(text)
        if wc < MIN_CHUNK_TOKENS:
            return
        has_code = bool(_CODE_FENCE_RE.search(text))
        qs = _quality_score(text, has_code)
        if qs < MIN_QUALITY_SCORE:
            return
        chunks.append(Chunk(
            chunk_id=_make_chunk_id(doc_id, text),
            doc_id=doc_id,
            chunk_index=chunk_index,
            title=title,
            category=category,
            source=source,
            heading_path=heading_path,
            heading_hierarchy=heading_hierarchy,
            chunk_type=ctype,
            text=text,
            has_code=has_code,
            code_language=clang or _primary_language(text),
            token_count=wc,
            quality_score=qs,
        ))
        chunk_index += 1

    def flush() -> None:
        nonlocal buf, buf_tokens
        if not buf:
            return
        joined = "\n\n".join(buf)

        stash: list[str] = []

        def _stash_fence(m: re.Match) -> str:
            stash.append(m.group(0))
            return f"\x00CF{len(stash) - 1}\x00"

        stashed = _CODE_FENCE_RE.sub(_stash_fence, joined)
        cleaned = clean_prose(stashed)
        for i, fence in enumerate(stash):
            cleaned = cleaned.replace(f"\x00CF{i}\x00", fence)

        emit(cleaned, "mixed" if stash else "prose")
        buf = []
        buf_tokens = 0

    for seg in segments:
        if seg.kind == "prose":
            para = clean_prose(seg.text)
            if not para:
                continue
            last_prose = para
            para_tokens = _approx_tokens(para)

            if buf_tokens + para_tokens > MAX_CHUNK_TOKENS and buf:
                prose_only = [p for p in buf if not p.startswith("```")]
                overlap_src = " ".join(prose_only)
                overlap = " ".join(overlap_src.split()[-OVERLAP_TOKENS:])
                flush()
                if overlap:
                    buf = [overlap]
                    buf_tokens = _approx_tokens(overlap)

            buf.append(para)
            buf_tokens += para_tokens

        else:
            code_fence = f"```{seg.language}\n{seg.text}```"
            code_tokens = _approx_tokens(seg.text)

            if code_tokens <= MAX_CHUNK_TOKENS:
                if buf_tokens + code_tokens > MAX_CHUNK_TOKENS and buf:
                    prose_only = [p for p in buf if not p.startswith("```")]
                    context_para = prose_only[-1] if prose_only else ""
                    flush()
                    if context_para:
                        buf = [context_para]
                        buf_tokens = _approx_tokens(context_para)
                buf.append(code_fence)
                buf_tokens += code_tokens
            else:
                flush()
                context = _last_n_sentences(last_prose, CODE_CONTEXT_SENTS) if last_prose else ""
                full_text = f"{context}\n\n{code_fence}" if context else code_fence
                emit(full_text, "code", seg.language)

    flush()
    return chunks


def process_document(md_path: Path) -> list[Chunk]:
    raw = md_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)

    doc_id   = md_path.stem
    title    = meta.get("title", doc_id.replace("-", " ").title())
    category = meta.get("category", "General")
    source   = meta.get("source", md_path.name)

    sections = split_into_sections(body)
    all_chunks: list[Chunk] = []
    chunk_index = 0

    for section in sections:
        if not section.body.strip():
            continue
        heading_path = " > ".join(section.ancestors + [section.heading]) if section.heading else title
        heading_hierarchy = section.ancestors + ([section.heading] if section.heading else [])
        segments = section_to_segments(section.body)
        new_chunks = _build_chunks_from_segments(
            segments=segments,
            heading_path=heading_path,
            heading_hierarchy=heading_hierarchy,
            doc_id=doc_id,
            title=title,
            category=category,
            source=source,
            start_index=chunk_index,
        )
        all_chunks.extend(new_chunks)
        chunk_index += len(new_chunks)

    seen: set[str] = set()
    deduped: list[Chunk] = []
    for c in all_chunks:
        if c.chunk_id not in seen:
            seen.add(c.chunk_id)
            deduped.append(c)

    return deduped


def build_embed_texts(chunks: list[Chunk]) -> list[str]:
    texts = []
    for c in chunks:
        if c.chunk_type == "code":
            lang_note = f" [{c.code_language}]" if c.code_language else ""
            context_header = f"[{c.category} > {c.title}] {c.heading_path} — code example{lang_note}"
        else:
            context_header = f"[{c.category} > {c.title}] {c.heading_path} ({c.chunk_type})"
        texts.append(f"{DOC_INSTRUCTION}\n{context_header}\n\n{c.text}")
    return texts


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Spring AI MCP — Ingestion Pipeline")
    p.add_argument("--docs-dir", default="data/docs")
    p.add_argument("--store-dir", default="store")
    p.add_argument("--batch-size", type=int, default=32)
    return p.parse_args()


def run_ingestion() -> None:
    args = parse_args()
    ROOT = Path(__file__).parent
    DOCS_DIR = ROOT / args.docs_dir
    STORE_DIR = ROOT / args.store_dir
    INDEX_PATH = STORE_DIR / "springai.index"
    META_PATH = STORE_DIR / "metadata.json"
    MANIFEST_PATH = STORE_DIR / "manifest.json"

    console.print(Panel.fit(
        f"[bold]Spring AI MCP — Ingestion Pipeline[/bold]\n"
        f"[dim]Model: {EMBED_MODEL} ({EMBED_DIM}-dim)[/dim]",
        border_style="cyan",
    ))

    if not DOCS_DIR.exists():
        console.print(f"[red]Error:[/red] docs directory not found: {DOCS_DIR}")
        sys.exit(1)

    md_files = sorted(DOCS_DIR.glob("*.md"))
    if not md_files:
        console.print(f"[red]Error:[/red] no .md files found in {DOCS_DIR}")
        sys.exit(1)

    STORE_DIR.mkdir(parents=True, exist_ok=True)
    console.print(f"  Found [cyan]{len(md_files)}[/cyan] markdown files\n")

    all_chunks: list[Chunk] = []
    parse_stats: list[dict] = []
    t_parse = time.perf_counter()

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        BarColumn(), TaskProgressColumn(), TimeElapsedColumn(), console=console,
    ) as progress:
        task = progress.add_task("[cyan]Parsing & chunking…", total=len(md_files))
        for md_path in md_files:
            doc_chunks = process_document(md_path)
            all_chunks.extend(doc_chunks)
            parse_stats.append({
                "file": md_path.name,
                "chunks": len(doc_chunks),
                "prose": sum(1 for c in doc_chunks if c.chunk_type == "prose"),
                "code": sum(1 for c in doc_chunks if c.chunk_type == "code"),
                "mixed": sum(1 for c in doc_chunks if c.chunk_type == "mixed"),
                "avg_quality": round(
                    sum(c.quality_score for c in doc_chunks) / max(len(doc_chunks), 1), 2
                ),
            })
            progress.advance(task)

    console.print(f"  Parse + chunk: {time.perf_counter() - t_parse:.1f}s\n")

    tbl = Table(
        title="Document Parse Summary", box=box.SIMPLE_HEAVY,
        show_lines=False, header_style="bold cyan",
    )
    tbl.add_column("File", style="dim", no_wrap=True)
    tbl.add_column("Total", justify="right")
    tbl.add_column("Prose", justify="right")
    tbl.add_column("Code", justify="right", style="yellow")
    tbl.add_column("Mixed", justify="right", style="green")
    tbl.add_column("Avg Quality", justify="right", style="magenta")

    for s in parse_stats:
        tbl.add_row(
            s["file"], str(s["chunks"]), str(s["prose"]),
            str(s["code"]), str(s["mixed"]), str(s["avg_quality"]),
        )
    tbl.add_section()
    tbl.add_row(
        "[bold]Total[/bold]",
        f"[bold]{len(all_chunks)}[/bold]",
        f"[bold]{sum(s['prose'] for s in parse_stats)}[/bold]",
        f"[bold]{sum(s['code'] for s in parse_stats)}[/bold]",
        f"[bold]{sum(s['mixed'] for s in parse_stats)}[/bold]",
        f"[bold]{round(sum(s['avg_quality'] for s in parse_stats) / max(len(parse_stats), 1), 2)}[/bold]",
    )
    console.print(tbl)

    if not all_chunks:
        console.print("[red]Error:[/red] no chunks produced.")
        sys.exit(1)

    console.print(f"\n[bold]Loading embedding model:[/bold] {EMBED_MODEL}")
    t_model = time.perf_counter()
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBED_MODEL)
    console.print(f"  Loaded in {time.perf_counter() - t_model:.1f}s\n")

    embed_texts = build_embed_texts(all_chunks)
    console.print(f"[bold]Encoding {len(embed_texts)} chunks (batch={args.batch_size})…[/bold]")
    t_embed = time.perf_counter()

    all_vecs: list[np.ndarray] = []
    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        BarColumn(), TaskProgressColumn(), TimeElapsedColumn(), console=console,
    ) as progress:
        task = progress.add_task("[green]Embedding…", total=len(embed_texts))
        for start in range(0, len(embed_texts), args.batch_size):
            batch = embed_texts[start: start + args.batch_size]
            vecs = model.encode(
                batch,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
            all_vecs.append(vecs.astype("float32"))
            progress.advance(task, advance=len(batch))

    matrix = np.vstack(all_vecs).astype("float32")
    console.print(f"  Embedded in {time.perf_counter() - t_embed:.1f}s — matrix {matrix.shape}\n")

    console.print("[bold]Building FAISS index…[/bold]")
    import faiss
    t_index = time.perf_counter()

    n = matrix.shape[0]
    if n < 1000:
        index = faiss.IndexFlatIP(EMBED_DIM)
        index_type = "IndexFlatIP (exact)"
    else:
        n_lists = max(4, int(8 * (n ** 0.5)))
        quantizer = faiss.IndexFlatIP(EMBED_DIM)
        index = faiss.IndexIVFFlat(quantizer, EMBED_DIM, n_lists, faiss.METRIC_INNER_PRODUCT)
        index.train(matrix)
        index_type = f"IndexIVFFlat (n_lists={n_lists})"

    index.add(matrix)
    faiss.write_index(index, str(INDEX_PATH))
    console.print(
        f"  [{index_type}] {index.ntotal} vectors → {INDEX_PATH} "
        f"({INDEX_PATH.stat().st_size // 1024} KB) in {time.perf_counter() - t_index:.2f}s\n"
    )

    console.print("[bold]Writing metadata…[/bold]")
    META_PATH.write_text(json.dumps([asdict(c) for c in all_chunks], indent=2, ensure_ascii=False))
    console.print(f"  {len(all_chunks)} chunk records → {META_PATH}\n")

    manifest = {
        "embed_model": EMBED_MODEL,
        "embed_dim": EMBED_DIM,
        "doc_instruction": DOC_INSTRUCTION,
        "query_instruction": QUERY_INSTRUCTION,
        "index_type": index_type,
        "total_docs": len(md_files),
        "total_chunks": len(all_chunks),
        "chunk_types": {
            "prose": sum(1 for c in all_chunks if c.chunk_type == "prose"),
            "code": sum(1 for c in all_chunks if c.chunk_type == "code"),
            "mixed": sum(1 for c in all_chunks if c.chunk_type == "mixed"),
        },
        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    console.print(f"  Manifest → {MANIFEST_PATH}\n")

    console.print(Panel.fit(
        f"[bold green]✓ Ingestion complete[/bold green]\n\n"
        f"  Docs processed  : [cyan]{len(md_files)}[/cyan]\n"
        f"  Total chunks    : [cyan]{len(all_chunks)}[/cyan]  "
        f"(prose={manifest['chunk_types']['prose']}, "
        f"code={manifest['chunk_types']['code']}, "
        f"mixed={manifest['chunk_types']['mixed']})\n"
        f"  Embed model     : [cyan]{EMBED_MODEL}[/cyan] ({EMBED_DIM}-dim)\n"
        f"  Index           : [cyan]{index_type}[/cyan]\n"
        f"  Index size      : [cyan]{INDEX_PATH.stat().st_size // 1024} KB[/cyan]\n\n"
        f"Next step:\n"
        f"  [bold]uvicorn server:app --host 0.0.0.0 --port 8000 --reload[/bold]",
        border_style="green",
    ))


if __name__ == "__main__":
    run_ingestion()
