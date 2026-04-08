#!/usr/bin/env python3
"""
Placeholder for seeding dummy worker profiles (CSV/Excel) into Chroma or a SQL DB.

When implemented: read from data/dummy/, write tenant metadata + optional synthetic chunks,
then run scripts/ingest_laws.py if chunk files are generated.
"""

from __future__ import annotations


def main() -> None:
    print(
        "seed_dummy_data: not implemented yet. "
        "Place profiles under data/dummy/ and extend this script."
    )


if __name__ == "__main__":
    main()
