#!/usr/bin/env python3
"""
Thin wrapper around QueryEngine (same behavior as query_engine CLI).

From repo root:
  python embedding/search_cli.py "fire exit requirements"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INDEX_DIR = REPO_ROOT / "embedding" / "index"


def main() -> int:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    parser = argparse.ArgumentParser(description="Semantic search (QueryEngine).")
    parser.add_argument("query", help="Search text (Bangla or English)")
    parser.add_argument("--index-dir", type=Path, default=DEFAULT_INDEX_DIR)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    try:
        from embedding.query_engine import QueryEngine

        engine = QueryEngine(args.index_dir, model_id=args.model)
        hits = engine.search(args.query, top_k=args.top_k)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1
    except ImportError:
        print("Install: pip install -r requirements.txt", file=sys.stderr)
        return 1

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
