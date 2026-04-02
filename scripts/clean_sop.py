"""
Template pipeline for an SOP PDF.
"""

from argparse import Namespace

from chunk_pipeline import run_pipeline


if __name__ == "__main__":
    run_pipeline(Namespace(
        input="raw/sop.pdf",
        source="SOP",
        skip_first=1,
        skip_last=0,
        skip_ranges=[],
        chunk_size=1000,
        overlap=100,
        output_dir="processed",
        output_name="sop_chunks.txt",
    ))
