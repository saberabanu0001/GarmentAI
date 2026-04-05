#!/usr/bin/env python3
"""
PDF → Markdown for the Labour Rules 2015 source (matches 1.1 labour law 2015 data).

Default paths (repo-relative):
  raw-data/1.1Labour-Rules-2015-English.pdf
  md data/1.1 labour law 2015.md

From repo root:
  python chunked-data-code/labour_law_2015_data_pdf_to_markdown.py

Override:
  python chunked-data-code/labour_law_2015_data_pdf_to_markdown.py \\
    --input path/to/other.pdf --output "md data/other.md"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pymupdf4llm

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_PDF = REPO_ROOT / "raw-data/1.1Labour-Rules-2015-English.pdf"
DEFAULT_MD = REPO_ROOT / "md data/1.1 labour law 2015.md"


def resolve_pdf(p: Path) -> Path:
    p = p.expanduser()
    if p.is_file():
        return p.resolve()
    alt = REPO_ROOT / p
    if alt.is_file():
        return alt.resolve()
    return p.resolve()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Labour Rules 2015 PDF → markdown (pymupdf4llm)."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_PDF,
        help=f"PDF path (default: {DEFAULT_PDF.name})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_MD,
        help='Markdown path (default: md data/1.1 labour law 2015.md)',
    )
    args = parser.parse_args()

    pdf = resolve_pdf(args.input)
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
