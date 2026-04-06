#!/usr/bin/env python3
"""
Build ChromaDB collections from chunked-data/*_chunks.txt using multilingual E5.

Uses embedding/collection_manifest.yaml for collection, language, RBAC, factory_id.

From repo root:
  python embedding/build_chroma.py
  python embedding/build_chroma.py --persist-dir embedding/chroma_data --clean
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import chromadb
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CHUNKS_DIR = REPO_ROOT / "chunked-data"
DEFAULT_PERSIST = REPO_ROOT / "embedding" / "chroma_data"
DEFAULT_MANIFEST = REPO_ROOT / "embedding" / "collection_manifest.yaml"
DEFAULT_MODEL = "intfloat/multilingual-e5-small"


def build_chroma(
    chunks_dir: Path,
    persist_dir: Path,
    manifest_path: Path,
    *,
    model: str = DEFAULT_MODEL,
    batch_size: int = 16,
    clean: bool = True,
) -> dict[str, int]:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    from embedding.e5_embedder import E5Embedder
    from embedding.manifest_loader import (
        chunk_uid,
        load_manifest,
        resolve_manifest_rule,
    )
    from embedding.parse_chunks import parse_chunks_file, passage_for_embedding

    rules = load_manifest(manifest_path)
    txt_files = sorted(chunks_dir.glob("*_chunks.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No *_chunks.txt under {chunks_dir}")

    if clean and persist_dir.exists():
        shutil.rmtree(persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(persist_dir))
    embedder = E5Embedder(model)

    counts: dict[str, int] = {}
    collections: dict[str, chromadb.Collection] = {}

    def get_collection(name: str) -> chromadb.Collection:
        if name not in collections:
            collections[name] = client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
        return collections[name]

    for path in txt_files:
        rule = resolve_manifest_rule(path.name, rules)
        records = parse_chunks_file(path)
        if not records:
            continue
        col = get_collection(rule.collection)
        passages = [passage_for_embedding(r) for r in records]
        emb = embedder.encode(passages, is_query=False, batch_size=batch_size)

        ids: list[str] = []
        embeddings: list[list[float]] = []
        documents: list[str] = []
        metadatas: list[dict[str, str | int | float | bool]] = []

        for rec, row_emb in zip(records, emb, strict=True):
            uid = chunk_uid(rule.factory_id, rec.chunks_filename, rec.chunk_id)
            ids.append(uid)
            embeddings.append(row_emb.astype(np.float32).tolist())
            documents.append(rec.text)
            metadatas.append(
                {
                    "chunk_uid": uid,
                    "chunk_id": int(rec.chunk_id),
                    "chunks_file": rec.chunks_filename,
                    "document_name": rec.document_name,
                    "source_name": rec.source_name,
                    "section": rec.section,
                    "page_start": rec.page_start,
                    "page_end": rec.page_end,
                    "doc_scope": rule.doc_scope,
                    "doc_category": rule.doc_category,
                    "language": rule.language,
                    "factory_id": rule.factory_id,
                    "allowed_roles": rule.allowed_roles_csv,
                    "collection": rule.collection,
                }
            )

        col.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        counts[rule.collection] = counts.get(rule.collection, 0) + len(ids)

    meta = {
        "model": model,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "chunks_dir": str(chunks_dir.resolve()),
        "manifest": str(manifest_path.resolve()),
        "collections": counts,
        "normalize_embeddings": True,
        "passage_prefix": "passage: ",
        "query_prefix": "query: ",
    }
    (persist_dir / "meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    return counts


def main() -> int:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    parser = argparse.ArgumentParser(description="Embed chunks into ChromaDB (E5, cosine).")
    parser.add_argument("--chunks-dir", type=Path, default=DEFAULT_CHUNKS_DIR)
    parser.add_argument("--persist-dir", type=Path, default=DEFAULT_PERSIST)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not delete existing persist-dir first (may duplicate ids on re-run)",
    )
    args = parser.parse_args()

    try:
        counts = build_chroma(
            args.chunks_dir,
            args.persist_dir,
            args.manifest,
            model=args.model,
            batch_size=args.batch_size,
            clean=not args.no_clean,
        )
    except Exception as e:
        print(e, file=sys.stderr)
        return 1

    print("Chroma collections:", json.dumps(counts, indent=2))
    print(f"Persisted to {args.persist_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
