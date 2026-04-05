#!/usr/bin/env python3
"""
Load embedding/index and run a single search (E5 query: prefix for multilingual).

From repo root:
  python embedding/search_cli.py "fire exit requirements"
  python embedding/search_cli.py "অগ্নি নির্বাপন" --top-k 3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INDEX_DIR = REPO_ROOT / "embedding" / "index"


def main() -> int:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    parser = argparse.ArgumentParser(description="Semantic search over embedded chunks.")
    parser.add_argument("query", help="Search text (e.g. Bangla or English)")
    parser.add_argument("--index-dir", type=Path, default=DEFAULT_INDEX_DIR)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--model",
        default=None,
        help="Override model id (default: read from meta.json)",
    )
    args = parser.parse_args()

    idx = args.index_dir
    emb_path = idx / "embeddings.npy"
    meta_path = idx / "meta.json"
    jsonl_path = idx / "chunks.jsonl"

    if not emb_path.is_file() or not jsonl_path.is_file():
        print(
            f"Index missing. Run first: python embedding/build_index.py\n"
            f"Expected: {emb_path} and {jsonl_path}",
            file=sys.stderr,
        )
        return 1

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Install: pip install sentence-transformers", file=sys.stderr)
        return 1

    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
    model_id = args.model or meta.get("model", "intfloat/multilingual-e5-small")
    q_prefix = meta.get("query_prefix", "query: ")

    print(f"Loading model {model_id} …")
    model = SentenceTransformer(model_id)

    matrix = np.load(emb_path)
    q = model.encode(
        [q_prefix + args.query],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )[0].astype(np.float32)

    scores = matrix @ q
    top_idx = np.argsort(-scores)[: args.top_k]

    rows: list[dict] = []
    with jsonl_path.open(encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))

    for rank, i in enumerate(top_idx, start=1):
        r = rows[int(i)]
        print(f"\n--- #{rank}  score={scores[int(i)]:.4f}  id={r['id']} ---")
        print(f"source: {r['source_name']} | doc: {r['document_name']}")
        print(f"section: {r['section']}")
        print(f"file: {r['chunks_file']} chunk_id={r['chunk_id']}")
        preview = r["text"].replace("\n", " ")[:400]
        print(f"text: {preview}…")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
