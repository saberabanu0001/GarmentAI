#!/usr/bin/env python3
"""
Compatibility: builds Chroma from data/chunked.

Prefer: python scripts/ingest_laws.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from backend.services.chroma_ingest import main

if __name__ == "__main__":
    raise SystemExit(main())
