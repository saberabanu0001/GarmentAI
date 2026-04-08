#!/usr/bin/env python3
"""
RAG CLI: Chroma + Ollama / Groq / Gemini.

From repo root:
  python embedding/rag_cli.py "your question" --role worker
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.core.config import get_settings
from backend.core.security import Role
from backend.services.llm_wrapper import BackendName
from backend.services.rag import rag_answer


def main() -> int:
    parser = argparse.ArgumentParser(description="RAG answer with Chroma + LLM.")
    parser.add_argument("question", help="User question (Bangla or English)")
    parser.add_argument("--role", default=Role.WORKER.value, help="RBAC role")
    parser.add_argument("--factory", default="", help="Tenant slug, e.g. good or risky")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--backend",
        choices=("ollama", "groq", "gemini"),
        default=None,
        help="Override LLM_BACKEND env",
    )
    parser.add_argument("--chroma-dir", type=Path, default=None)
    parser.add_argument(
        "--no-worker-tone",
        action="store_true",
        help="Use neutral system prompt (no Bangla/English worker wording)",
    )
    args = parser.parse_args()

    try:
        role = Role(args.role)
    except ValueError:
        print(
            f"Invalid role {args.role!r}. Use one of: {[r.value for r in Role]}",
            file=sys.stderr,
        )
        return 1

    chroma_dir = args.chroma_dir or get_settings().chroma_dir
    backend: BackendName | None = args.backend

    try:
        reply, hits = rag_answer(
            args.question,
            role=role,
            factory_id=args.factory,
            top_k=args.top_k,
            backend=backend,
            chroma_dir=chroma_dir,
            audience_worker_simple=not args.no_worker_tone,
        )
    except Exception as e:
        print(e, file=sys.stderr)
        return 1

    print("\n--- Retrieved chunks ---")
    for h in hits:
        print(f"  #{h.rank} {h.collection} | {h.similarity:.4f} | {h.chunk_uid}")
    print("\n--- Answer ---\n")
    print(reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
