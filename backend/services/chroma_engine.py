#!/usr/bin/env python3
"""
Query ChromaDB collections with E5 query embeddings, RBAC post-filter, and merge tie-break.

From repo root:
  python -m backend.services.chroma_engine "salary" --role worker --factory risky --top-k 5
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
import numpy as np

from backend.core.config import get_settings
from backend.core.security import Role, role_may_access
from backend.services.merge_policy import merge_tier

DEFAULT_MODEL = "intfloat/multilingual-e5-small"


def collection_names_for_factory(factory_id: str) -> list[str]:
    names = ["global_laws", "compliance_standards"]
    fid = (factory_id or "").strip()
    if fid:
        names.append(f"factory_{fid}_docs")
    return names


@dataclass
class ChromaHit:
    rank: int
    similarity: float
    distance: float
    chunk_uid: str
    chunk_id: int
    chunks_file: str
    document_name: str
    source_name: str
    section: str
    page_start: str
    page_end: str
    collection: str
    doc_scope: str
    doc_category: str
    language: str
    factory_id: str
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "similarity": self.similarity,
            "distance": self.distance,
            "chunk_uid": self.chunk_uid,
            "chunk_id": self.chunk_id,
            "chunks_file": self.chunks_file,
            "document_name": self.document_name,
            "source_name": self.source_name,
            "section": self.section,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "collection": self.collection,
            "doc_scope": self.doc_scope,
            "doc_category": self.doc_category,
            "language": self.language,
            "factory_id": self.factory_id,
            "text": self.text,
        }


class ChromaQueryEngine:
    def __init__(
        self,
        persist_dir: Path | None = None,
        *,
        model_id: str | None = None,
    ) -> None:
        self.persist_dir = Path(persist_dir) if persist_dir else get_settings().chroma_dir
        meta_path = self.persist_dir / "meta.json"
        if not self.persist_dir.is_dir() or not meta_path.is_file():
            raise FileNotFoundError(
                f"Chroma index not found. Run: python scripts/ingest_laws.py\n"
                f"Expected: {meta_path}"
            )

        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        self.model_id = model_id or meta.get("model", DEFAULT_MODEL)
        self._client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._embedder: Any | None = None

    def _ensure_embedder(self) -> None:
        if self._embedder is not None:
            return
        from backend.services.embedder import E5Embedder

        self._embedder = E5Embedder(self.model_id)

    def search(
        self,
        query: str,
        *,
        role: Role | str,
        factory_id: str = "",
        top_k: int = 5,
        per_collection_k: int | None = None,
    ) -> list[ChromaHit]:
        if not isinstance(role, Role):
            role = Role(role)

        self._ensure_embedder()
        assert self._embedder is not None
        qv = self._embedder.encode([query], is_query=True, batch_size=1)[0]
        q_list = qv.astype(np.float32).tolist()

        k_each = per_collection_k or max(top_k * 4, 16)
        candidates: list[dict[str, Any]] = []

        for cname in collection_names_for_factory(factory_id):
            try:
                col = self._client.get_collection(cname)
            except Exception:
                continue
            raw = col.query(
                query_embeddings=[q_list],
                n_results=k_each,
                include=["metadatas", "distances", "documents"],
            )
            ids = raw.get("ids", [[]])[0]
            dists = raw.get("distances", [[]])[0]
            metas = raw.get("metadatas", [[]])[0]
            docs = raw.get("documents", [[]])[0]
            for _id, dist, meta, doc in zip(ids, dists, metas, docs, strict=True):
                if meta is None:
                    continue
                d = float(dist)
                sim = 1.0 - d
                allowed = str(meta.get("allowed_roles", ""))
                if not role_may_access(allowed, role):
                    continue
                doc_scope = str(meta.get("doc_scope", ""))
                candidates.append(
                    {
                        "similarity": sim,
                        "distance": d,
                        "meta": meta,
                        "document": doc or "",
                        "collection": cname,
                        "doc_scope": doc_scope,
                    }
                )

        candidates.sort(
            key=lambda x: (-x["similarity"], merge_tier(x["doc_scope"])),
        )

        hits: list[ChromaHit] = []
        for rank, cdt in enumerate(candidates[:top_k], start=1):
            m = cdt["meta"]
            hits.append(
                ChromaHit(
                    rank=rank,
                    similarity=float(cdt["similarity"]),
                    distance=float(cdt["distance"]),
                    chunk_uid=str(m.get("chunk_uid", "")),
                    chunk_id=int(m.get("chunk_id", -1)),
                    chunks_file=str(m.get("chunks_file", "")),
                    document_name=str(m.get("document_name", "")),
                    source_name=str(m.get("source_name", "")),
                    section=str(m.get("section", "")),
                    page_start=str(m.get("page_start", "")),
                    page_end=str(m.get("page_end", "")),
                    collection=str(cdt["collection"]),
                    doc_scope=str(m.get("doc_scope", "")),
                    doc_category=str(m.get("doc_category", "")),
                    language=str(m.get("language", "")),
                    factory_id=str(m.get("factory_id", "")),
                    text=str(cdt["document"] or ""),
                )
            )
        return hits


def main() -> int:
    parser = argparse.ArgumentParser(description="Chroma + E5 vector search with RBAC.")
    parser.add_argument("query", help="User question (Bangla or English)")
    parser.add_argument("--persist-dir", type=Path, default=None)
    parser.add_argument("--factory", default="", help="Tenant slug, e.g. good or risky")
    _requesting_roles = [r for r in Role if r is not Role.ALL]
    parser.add_argument(
        "--role",
        type=str,
        default=Role.WORKER.value,
        choices=[r.value for r in _requesting_roles],
        help="Requesting role (canonical string)",
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    try:
        engine = ChromaQueryEngine(args.persist_dir, model_id=args.model)
        hits = engine.search(
            args.query,
            role=Role(args.role),
            factory_id=args.factory,
            top_k=args.top_k,
        )
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1
    except Exception as e:
        print(e, file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps([h.to_dict() for h in hits], ensure_ascii=False, indent=2))
        return 0

    for h in hits:
        print(f"\n--- #{h.rank}  sim={h.similarity:.4f}  coll={h.collection} ---")
        print(f"chunk_uid={h.chunk_uid} | {h.source_name} | {h.document_name}")
        print(f"section: {h.section} | lang={h.language}")
        preview = h.text.replace("\n", " ")[:400]
        print(f"text: {preview}…")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
