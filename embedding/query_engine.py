#!/usr/bin/env python3
"""
Query engine: embed user question with multilingual E5 (query: prefix),
score against indexed passage vectors (cosine = dot product), return top-k chunks.

Library:
  from embedding.query_engine import QueryEngine
  engine = QueryEngine()
  hits = engine.search("weekly holiday", top_k=5)

CLI:
  python embedding/query_engine.py "fire safety exit" --top-k 4
  python embedding/query_engine.py "question" --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INDEX_DIR = REPO_ROOT / "embedding" / "index"
DEFAULT_MODEL = "intfloat/multilingual-e5-small"


@dataclass
class SearchHit:
    rank: int
    score: float
    id: int
    chunk_id: int
    chunks_file: str
    document_name: str
    source_name: str
    section: str
    page_start: str
    page_end: str
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "score": self.score,
            "id": self.id,
            "chunk_id": self.chunk_id,
            "chunks_file": self.chunks_file,
            "document_name": self.document_name,
            "source_name": self.source_name,
            "section": self.section,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "text": self.text,
        }


def _load_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


class QueryEngine:
    """Connects user queries to precomputed passage embeddings (build_index.py)."""

    def __init__(
        self,
        index_dir: Path | None = None,
        *,
        model_id: str | None = None,
    ) -> None:
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))

        self.index_dir = Path(index_dir) if index_dir else DEFAULT_INDEX_DIR
        self._emb_path = self.index_dir / "embeddings.npy"
        self._meta_path = self.index_dir / "meta.json"
        self._jsonl_path = self.index_dir / "chunks.jsonl"

        if not self._emb_path.is_file() or not self._jsonl_path.is_file():
            raise FileNotFoundError(
                f"Index not found. Run: python embedding/build_index.py\n"
                f"Missing: {self._emb_path} or {self._jsonl_path}"
            )

        meta: dict[str, Any] = {}
        if self._meta_path.is_file():
            meta = json.loads(self._meta_path.read_text(encoding="utf-8"))

        self.model_id = model_id or meta.get("model", DEFAULT_MODEL)
        self._matrix: np.ndarray | None = None
        self._rows: list[dict[str, Any]] | None = None
        self._embedder: Any = None

    def _ensure_loaded(self) -> None:
        if self._matrix is not None and self._rows is not None:
            return
        self._matrix = np.load(self._emb_path)
        self._rows = _load_jsonl_rows(self._jsonl_path)
        n = self._matrix.shape[0]
        if len(self._rows) != n:
            raise ValueError(
                f"Row count mismatch: embeddings {n} vs chunks.jsonl {len(self._rows)}"
            )

    def _ensure_embedder(self) -> None:
        if self._embedder is not None:
            return
        from embedding.e5_embedder import E5Embedder

        self._embedder = E5Embedder(self.model_id)

    def search(self, query: str, *, top_k: int = 5) -> list[SearchHit]:
        self._ensure_loaded()
        self._ensure_embedder()

        assert self._matrix is not None and self._rows is not None
        k = max(1, min(top_k, len(self._rows)))

        q_vec = self._embedder.encode([query], is_query=True, batch_size=1)[0]
        scores = self._matrix @ q_vec
        top_indices = np.argsort(-scores)[:k]

        hits: list[SearchHit] = []
        for rank, i in enumerate(top_indices, start=1):
            i_int = int(i)
            r = self._rows[i_int]
            hits.append(
                SearchHit(
                    rank=rank,
                    score=float(scores[i_int]),
                    id=int(r["id"]),
                    chunk_id=int(r["chunk_id"]),
                    chunks_file=str(r["chunks_file"]),
                    document_name=str(r["document_name"]),
                    source_name=str(r["source_name"]),
                    section=str(r["section"]),
                    page_start=str(r["page_start"]),
                    page_end=str(r["page_end"]),
                    text=str(r["text"]),
                )
            )
        return hits


def main() -> int:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    parser = argparse.ArgumentParser(
        description="Query engine: question → top similar chunks (E5 multilingual)."
    )
    parser.add_argument("query", help="User question (Bangla or English)")
    parser.add_argument("--index-dir", type=Path, default=DEFAULT_INDEX_DIR)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print hits as JSON",
    )
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    try:
        engine = QueryEngine(args.index_dir, model_id=args.model)
        hits = engine.search(args.query, top_k=args.top_k)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1
    except ImportError:
        print("Install: pip install -r requirements.txt", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps([h.to_dict() for h in hits], ensure_ascii=False, indent=2))
        return 0

    for h in hits:
        print(f"\n--- #{h.rank}  score={h.score:.4f}  id={h.id} ---")
        print(f"source: {h.source_name} | doc: {h.document_name}")
        print(f"section: {h.section}")
        print(f"file: {h.chunks_file} chunk_id={h.chunk_id}")
        preview = h.text.replace("\n", " ")[:400]
        print(f"text: {preview}…")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
