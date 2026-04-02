"""
Preconfigured pipeline for the compliance practices paper.
"""

from argparse import Namespace

from chunk_pipeline import run_pipeline


if __name__ == "__main__":
    run_pipeline(Namespace(
        input="raw/Compliance_Practices_in_Garment_Industries_in_Dhak.pdf",
        source="Compliance",
        skip_first=1,
        skip_last=0,
        skip_ranges=["13-17"],
        chunk_size=1000,
        overlap=100,
        output_dir="processed",
        output_name="compliance_chunks.txt",
    ))
