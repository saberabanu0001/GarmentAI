"""
Preconfigured pipeline for the sewing machine manual.
"""

from argparse import Namespace

from chunk_pipeline import run_pipeline


if __name__ == "__main__":
    run_pipeline(Namespace(
        input="raw/JUKI DU-1181N Manual _ ManualsLib.pdf",
        source="Machine Manual",
        skip_first=2,
        skip_last=0,
        skip_ranges=[],
        chunk_size=1000,
        overlap=100,
        output_dir="processed",
        output_name="machine_manual_chunks.txt",
    ))
