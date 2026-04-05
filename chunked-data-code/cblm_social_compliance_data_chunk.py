#!/usr/bin/env python3
"""Chunk: md data/4 CBLM social compliance data.md → chunked-data/*CBLM*."""
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
        "md data/4 CBLM social compliance data.md",
        "--source-name",
        "CBLM",
        "--document-name",
        "CBLM Social Compliance and Environmental Management",
    ] + sys.argv[1:]
    runpy.run_path(str(_ENGINE), run_name="__main__")
