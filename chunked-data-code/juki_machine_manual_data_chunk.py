#!/usr/bin/env python3
"""Chunk: md data/5 JUKI machine manual data.md → chunked-data/*JUKI*."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
_ENGINE = _DIR / "markdown_langchain_chunker.py"

if __name__ == "__main__":
    sys.argv = [
        str(_ENGINE),
        "--input",
        "md data/5 JUKI machine manual data.md",
        "--source-name",
        "Machine Manual",
        "--document-name",
        "JUKI DU-1181N Sewing Machine Manual",
    ] + sys.argv[1:]
    runpy.run_path(str(_ENGINE), run_name="__main__")
