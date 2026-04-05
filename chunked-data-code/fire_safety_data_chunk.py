#!/usr/bin/env python3
"""
Chunk: md data/2 fire safety data.md
  → chunked-data/Fire_Safety_Manual_for_RMG_Buildings_chunks.txt (+ manifest).

From repo root:
  python chunked-data-code/fire_safety_data_chunk.py
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
        "md data/2 fire safety data.md",
        "--source-name",
        "Fire Safety",
        "--document-name",
        "Fire Safety Manual for RMG Buildings",
    ] + extra
    runpy.run_path(str(_ENGINE), run_name="__main__")
