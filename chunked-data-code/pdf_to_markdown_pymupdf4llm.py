#!/usr/bin/env python3
"""
Extract a PDF to markdown using pymupdf4llm (tables/structure preserved).

Example:
  python chunked-data-code/pdf_to_markdown_pymupdf4llm.py \\
    --input raw-data/1.1Labour-Rules-2015-English_Unofficial.pdf \\
    --output "md data/1.1 labour law 2015.md"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pymupdf4llm

REPO_ROOT = Path(__file__).resolve().parent.parent


def resolve_path(p: Path) -> Path:
    p = p.expanduser()
    if p.is_file() or p.parent.exists():
        return p.resolve()
    alt = REPO_ROOT / p
    if alt.is_file():
        return alt.resolve()
    return p.resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description="PDF → Markdown via pymupdf4llm.")
    parser.add_argument("--input", type=Path, required=True, help="Path to PDF")
    parser.add_argument("--output", type=Path, required=True, help="Path to .md file")
    args = parser.parse_args()

    pdf = resolve_path(args.input)
    if not pdf.is_file():
        print(f"Error: PDF not found: {args.input}", file=sys.stderr)
        return 1

    out = args.output
    if not out.is_absolute():
        out = (REPO_ROOT / out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"Reading: {pdf}")
    md_text = pymupdf4llm.to_markdown(str(pdf))
    out.write_text(md_text, encoding="utf-8")
    print(f"Wrote {len(md_text)} chars → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
