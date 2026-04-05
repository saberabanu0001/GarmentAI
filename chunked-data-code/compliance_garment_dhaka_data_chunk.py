#!/usr/bin/env python3
"""Chunk: md data/3 compliance garment dhaka data.md → chunked-data/*Compliance*."""
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
        "md data/3 compliance garment dhaka data.md",
        "--source-name",
        "Compliance Garment Dhaka",
        "--document-name",
        "Compliance Practices in Garment Industries Dhaka",
    ] + sys.argv[1:]
    runpy.run_path(str(_ENGINE), run_name="__main__")
