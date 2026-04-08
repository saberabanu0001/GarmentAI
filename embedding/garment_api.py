#!/usr/bin/env python3
"""Launch FastAPI: `uvicorn backend.main:app` from repository root."""

from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__":
    repo = Path(__file__).resolve().parent.parent
    import subprocess

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "5050",
    ]
    raise SystemExit(subprocess.call(cmd, cwd=str(repo)))
