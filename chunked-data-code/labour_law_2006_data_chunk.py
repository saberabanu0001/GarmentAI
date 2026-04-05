#!/usr/bin/env python3
"""
Chunk: md data/1 labour law 2006 data.md
  → chunked-data/Bangladesh_Labour_Act_2006_chunks.txt (+ manifest).

From repo root:
  python chunked-data-code/labour_law_2006_data_chunk.py
Extra args are passed through (e.g. --chunk-size 3000).
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
_ENGINE = _DIR / "markdown_langchain_chunker.py"

if __name__ == "__main__":
    extra = sys.argv[1:]
    sys.argv = [
        str(_ENGINE),
        "--input",
        "md data/1 labour law 2006 data.md",
        "--source-name",
        "Labour Law",
        "--document-name",
        "Bangladesh Labour Act 2006",
    ] + extra
    runpy.run_path(str(_ENGINE), run_name="__main__")
