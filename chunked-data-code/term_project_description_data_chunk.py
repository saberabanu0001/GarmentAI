#!/usr/bin/env python3
"""Chunk: md data/6 term project description data.md → chunked-data/*Term_Project*."""
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
        "md data/6 term project description data.md",
        "--source-name",
        "Course Information",
        "--document-name",
        "Term Project Description",
    ] + sys.argv[1:]
    runpy.run_path(str(_ENGINE), run_name="__main__")
