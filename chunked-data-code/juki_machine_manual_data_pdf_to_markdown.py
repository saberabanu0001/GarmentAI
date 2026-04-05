#!/usr/bin/env python3
"""
PDF → Markdown: JUKI DU-1181N machine manual.

Defaults:
  raw-data/JUKI DU-1181N Manual _ ManualsLib.pdf
  md data/5 JUKI machine manual data.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pymupdf4llm

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PDF = REPO_ROOT / "raw-data/JUKI DU-1181N Manual _ ManualsLib.pdf"
DEFAULT_MD = REPO_ROOT / "md data/5 JUKI machine manual data.md"


def resolve_pdf(p: Path) -> Path:
    p = p.expanduser()
    if p.is_file():
        return p.resolve()
    alt = REPO_ROOT / p
    if alt.is_file():
        return alt.resolve()
    return p.resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description="JUKI manual PDF → markdown.")
    parser.add_argument("--input", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--output", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()
    pdf = resolve_pdf(args.input)
    if not pdf.is_file():
        print(f"Error: PDF not found: {args.input}", file=sys.stderr)
        return 1
    out = args.output if args.output.is_absolute() else (REPO_ROOT / args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f"Reading: {pdf}")
    out.write_text(pymupdf4llm.to_markdown(str(pdf)), encoding="utf-8")
    print(f"Wrote → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
