"""
Preconfigured pipeline for the training manual.
"""

from argparse import Namespace

from chunk_pipeline import run_pipeline


if __name__ == "__main__":
    run_pipeline(Namespace(
        input="raw/Final_CBLM-Social-Com-Env-Mgt_23-Nov-25_1766467717618.pdf",
        source="Training",
        skip_first=2,
        skip_last=0,
        skip_ranges=[],
        chunk_size=1000,
        overlap=100,
        output_dir="processed",
        output_name="training_chunks.txt",
    ))
