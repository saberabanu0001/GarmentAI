#!/usr/bin/env python3
"""
Build embedding index from chunked-data/*_chunks.txt using multilingual E5 (CPU-friendly).

Default model: intfloat/multilingual-e5-small (384-dim, good for Bangla queries later).

From repo root:
  pip install -r requirements.txt
  python embedding/build_index.py

Outputs (under embedding/index/):
  embeddings.npy   — float32 [N, dim], L2-normalized (cosine = dot product)
  chunks.jsonl     — one JSON object per line (metadata + full text)
  meta.json        — model id, dim, counts, paths

Search demo:
  python embedding/search_cli.py "your question in any language"
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CHUNKS_DIR = REPO_ROOT / "chunked-data"
DEFAULT_OUT_DIR = REPO_ROOT / "embedding" / "index"
DEFAULT_MODEL = "intfloat/multilingual-e5-small"


def main() -> int:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    parser = argparse.ArgumentParser(description="Embed all *_chunks.txt into numpy + jsonl.")
    parser.add_argument(
        "--chunks-dir",
        type=Path,
        default=DEFAULT_CHUNKS_DIR,
        help="Folder containing *_chunks.txt",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Writes embeddings.npy, chunks.jsonl, meta.json",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="sentence-transformers model id",
    )
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    chunks_dir = args.chunks_dir
    if not chunks_dir.is_dir():
        print(f"Error: chunks dir not found: {chunks_dir}", file=sys.stderr)
        return 1

    # Import after argparse so --help works without torch installed
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        print("Install: pip install sentence-transformers", file=sys.stderr)
        print(e, file=sys.stderr)
        return 1

    from embedding.parse_chunks import load_all_chunks, passage_for_embedding

    records = load_all_chunks(chunks_dir)
    if not records:
        print(f"No chunks found under {chunks_dir} (*_chunks.txt).", file=sys.stderr)
        return 1

    print(f"Loading model {args.model} …")
    model = SentenceTransformer(args.model)
    passages = [passage_for_embedding(r) for r in records]

    print(f"Encoding {len(passages)} chunks (batch_size={args.batch_size}) …")
    emb = model.encode(
        passages,
        batch_size=args.batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    emb = np.asarray(emb, dtype=np.float32)

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    np.save(out_dir / "embeddings.npy", emb)

    jsonl_path = out_dir / "chunks.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for i, rec in enumerate(records):
            row = {
                "id": i,
                "chunk_id": rec.chunk_id,
                "chunks_file": rec.chunks_filename,
                "document_name": rec.document_name,
                "source_name": rec.source_name,
                "page_start": rec.page_start,
                "page_end": rec.page_end,
                "section": rec.section,
                "text": rec.text,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    meta = {
        "model": args.model,
        "embedding_dim": int(emb.shape[1]),
        "num_chunks": int(emb.shape[0]),
        "chunks_dir": str(chunks_dir.resolve()),
        "built_at": datetime.now(timezone.utc).isoformat(),
        "normalize_embeddings": True,
        "passage_prefix": "passage: ",
        "query_prefix": "query: ",
    }
    (out_dir / "meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    print(f"Wrote {emb.shape[0]} x {emb.shape[1]} → {out_dir / 'embeddings.npy'}")
    print(f"Wrote {jsonl_path.name}")
    print(f"Wrote meta.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
