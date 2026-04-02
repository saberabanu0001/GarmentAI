"""
Preconfigured pipeline for the fire safety manual.
"""

from argparse import Namespace

from chunk_pipeline import run_pipeline


if __name__ == "__main__":
    run_pipeline(Namespace(
        input="raw/RSC-Fire-Safety-Manual-for-RMG-Buildings.pdf",
        source="Fire Safety",
        skip_first=3,
        skip_last=1,
        skip_ranges=["26-42"],
        chunk_size=1000,
        overlap=100,
        output_dir="processed",
        output_name="fire_safety_chunks.txt",
    ))
