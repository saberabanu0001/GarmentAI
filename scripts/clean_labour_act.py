"""
Preconfigured pipeline for the Bangladesh Labour Act PDF.
"""

from argparse import Namespace

from chunk_pipeline import run_pipeline


if __name__ == "__main__":
    run_pipeline(Namespace(
        input="raw/Bangladesh-Labour-Act-2006_English-Upto-2018.pdf",
        source="Labour Law",
        skip_first=0,
        skip_last=1,
        skip_ranges=[],
        chunk_size=1000,
        overlap=100,
        output_dir="processed",
        output_name="labour_law_chunks.txt",
    ))
