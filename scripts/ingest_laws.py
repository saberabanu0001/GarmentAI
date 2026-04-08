#!/usr/bin/env python3
"""
Build / refresh the local Chroma index from data/chunked.

From repository root:
  python scripts/ingest_laws.py
  python scripts/ingest_laws.py --no-clean
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
