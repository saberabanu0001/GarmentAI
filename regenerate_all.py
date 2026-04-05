"""
Re-generate all markdown-based chunk files from chunked-data-code/.
Run from the Experiment/ directory with the venv active if needed.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHUNK_SCRIPTS = [
    "chunked-data-code/labour_law_2006_data_chunk.py",
    "chunked-data-code/labour_law_2015_data_chunk.py",
    "chunked-data-code/fire_safety_data_chunk.py",
]


def main() -> None:
    print("Regenerating chunk outputs...\n")
    if not (ROOT / "chunked-data-code" / "markdown_langchain_chunker.py").is_file():
        print("Error: run from the Experiment/ directory (chunked-data-code missing).")
        sys.exit(1)

    for rel in CHUNK_SCRIPTS:
        script = ROOT / rel
        if not script.is_file():
            print(f"Skipping (missing): {rel}")
            continue
        print(f"Running {rel}...")
        r = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        if r.returncode == 0:
            print(f"  OK: {rel}")
        else:
            print(f"  Error: {rel}")
            print(r.stdout)
            print(r.stderr, file=sys.stderr)
        print("-" * 40)

    print("\nAll done!")


if __name__ == "__main__":
    main()
