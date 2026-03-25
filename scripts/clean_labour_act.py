"""
preprocess.py – General-purpose data preprocessing pipeline
============================================================
Workflow: Document → Text Extraction → Cleaning → Chunking → Save

Usage:
    python preprocess.py --input raw/myfile.pdf --source "Labour Law"
    python preprocess.py --input raw/myfile.pdf --source "Fire Safety" --chunk_size 1000

Supports: PDF files
Output:   processed/<source_name>_chunks.txt
"""

import re
import os
import sys
import argparse
import fitz  # PyMuPDF


# ─────────────────────────────────────────────────────────────────
# ARGUMENT PARSING
# ─────────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Preprocess a PDF into clean text chunks for a knowledge base."
    )
    parser.add_argument(
        "--input", required=True,
        help="Path to the input PDF file (e.g. raw/fire_safety.pdf)"
    )
    parser.add_argument(
        "--source", required=True,
        help="Short name for this data source (e.g. 'Fire Safety', 'Labour Law')"
    )
    parser.add_argument(
        "--skip_first", type=int, default=0,
        help="Number of pages to skip at the START (cover, TOC). Default: 0"
    )
    parser.add_argument(
        "--skip_last", type=int, default=0,
        help="Number of pages to skip at the END (colophon, contact). Default: 0"
    )
    parser.add_argument(
        "--skip_ranges", nargs="*", default=[],
        metavar="START-END",
        help="Page ranges to skip (1-indexed, inclusive). "
             "Example: --skip_ranges 26-42 to skip appendix forms"
    )
    parser.add_argument(
        "--chunk_size", type=int, default=1000,
        help="Target characters per chunk. Default: 1000"
    )
    parser.add_argument(
        "--overlap", type=int, default=100,
        help="Overlap characters between chunks for context. Default: 100"
    )
    parser.add_argument(
        "--output_dir", default="processed",
        help="Output directory. Default: processed/"
    )
    return parser.parse_args()


# ─────────────────────────────────────────────────────────────────
# STEP 1: TEXT EXTRACTION
# ─────────────────────────────────────────────────────────────────
def extract_text(pdf_path, skip_pages: set) -> tuple[str, int, list]:
    doc = fitz.open(pdf_path)
    total = len(doc)
    parts = []
    kept = []

    for i, page in enumerate(doc):
        if i in skip_pages:
            continue
        text = page.get_text()
        if text.strip():
            parts.append(text)
            kept.append(i + 1)

    doc.close()
    return "\n".join(parts), total, kept


def build_skip_set(total_pages, skip_first, skip_last, skip_ranges):
    """Build a set of 0-indexed page numbers to skip."""
    skip = set()
    skip.update(range(0, skip_first))                        # leading pages
    skip.update(range(total_pages - skip_last, total_pages)) # trailing pages
    for r in skip_ranges:
        try:
            a, b = r.split("-")
            # Convert 1-indexed to 0-indexed
            skip.update(range(int(a) - 1, int(b)))
        except ValueError:
            print(f"  ⚠ Could not parse skip range: '{r}' — skipping it.")
    return skip


# ─────────────────────────────────────────────────────────────────
# STEP 2: CLEANING
# ─────────────────────────────────────────────────────────────────
def clean_text(text: str) -> str:
    # Remove spaced-letter logo from PDF graphics layer
    text = re.sub(r'\b([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])\b[^\n]*\n?', '', text)

    # Remove standalone page numbers (1–3 digit number alone on a line)
    text = re.sub(r'^\s*\d{1,3}\s*$', '', text, flags=re.MULTILINE)

    # Remove "Page X of Y" markers
    text = re.sub(r'Page\s+\d+\s*(of\s+\d+)?', '', text, flags=re.IGNORECASE)

    # Remove URLs
    text = re.sub(r'(https?://|www\.)\S+', '', text)

    # Remove non-ASCII characters (PDF artefacts)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    # Remove separator lines (long dashes, equals, underscores, dot-leaders)
    text = re.sub(r'[-=_]{3,}', '', text)
    text = re.sub(r'\.{4,}', '', text)

    # Collapse whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Drop very short lines (< 3 chars) — 
    lines = [ln for ln in text.split('\n')
             if len(ln.strip()) >= 3 or ln.strip() == '']
    return '\n'.join(lines).strip()


# ─────────────────────────────────────────────────────────────────
# STEP 3: CHUNKING
# ─────────────────────────────────────────────────────────────────
def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split text into chunks of ~chunk_size characters.
    Prefers paragraph/sentence boundaries for clean breaks.
    Advances by at least (chunk_size - overlap) each iteration.
    """
    chunks = []
    length = len(text)
    pos = 0
    min_step = chunk_size - overlap

    while pos < length:
        end = min(pos + chunk_size, length)

        if end >= length:
            chunk = text[pos:].strip()
            if chunk:
                chunks.append(chunk)
            break

        search_start = pos + max(min_step // 2, 1)

        para = text.rfind('\n\n', search_start, end)
        sent = max(
            text.rfind('. ', search_start, end),
            text.rfind('.\n', search_start, end),
        )
        nl = text.rfind('\n', search_start, end)

        if para > 0:
            boundary = para
        elif sent > 0:
            boundary = sent + 1
        elif nl > 0:
            boundary = nl
        else:
            boundary = end

        chunk = text[pos:boundary].strip()
        if chunk:
            chunks.append(chunk)

        pos = boundary - overlap
        if pos <= 0:
            pos = boundary


    return chunks


# ─────────────────────────────────────────────────────────────────
# STEP 4: SAVE OUTPUT
# ─────────────────────────────────────────────────────────────────
def save_chunks(chunks, output_path, source_name, pdf_path, kept_pages,
                total_pages, chunk_size, overlap):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"SOURCE  : {source_name}\n")
        f.write(f"FILE    : {os.path.basename(pdf_path)}\n")
        f.write(f"PAGES   : {len(kept_pages)} kept of {total_pages} total\n")
        f.write(f"CHUNKS  : {len(chunks)}  "
                f"| Size: {chunk_size} chars  | Overlap: {overlap} chars\n")
        f.write("=" * 60 + "\n\n")
        for i, chunk in enumerate(chunks, 1):
            f.write(f"[CHUNK {i}]\n{chunk}\n\n")


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────
def main():
    args = parse_args()

    # Validate input file
    if not os.path.isfile(args.input):
        print(f"❌ File not found: {args.input}")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    # Output filename derived from source name
    safe_name = re.sub(r'[^a-zA-Z0-9]+', '_', args.source).lower().strip('_')
    output_path = os.path.join(args.output_dir, f"{safe_name}_chunks.txt")

    print("=" * 60)
    print(f"  Source   : {args.source}")
    print(f"  Input    : {args.input}")
    print(f"  Output   : {output_path}")
    print("=" * 60)

    # ── Step 1: Extract ──────────────────────────────────────────
    print("\n[1/4] Extracting text from PDF...")

    # Need total pages first to resolve skip_last
    tmp_doc = fitz.open(args.input)
    total_pages = len(tmp_doc)
    tmp_doc.close()

    skip_pages = build_skip_set(
        total_pages, args.skip_first, args.skip_last, args.skip_ranges
    )

    raw_text, total_pages, kept_pages = extract_text(args.input, skip_pages)
    print(f"  Pages kept  : {len(kept_pages)} / {total_pages}")
    print(f"  Raw chars   : {len(raw_text):,}")

    # ── Step 2: Clean ────────────────────────────────────────────
    print("\n[2/4] Cleaning text...")
    cleaned = clean_text(raw_text)
    removed = len(raw_text) - len(cleaned)
    print(f"  Clean chars : {len(cleaned):,}  (removed {removed:,} = "
          f"{removed/len(raw_text)*100:.1f}%)")

    # ── Step 3: Chunk ────────────────────────────────────────────
    print("\n[3/4] Chunking...")
    chunks = chunk_text(cleaned, args.chunk_size, args.overlap)
    avg_len = sum(len(c) for c in chunks) // max(len(chunks), 1)
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Avg length  : {avg_len} chars")

    # ── Step 4: Save ─────────────────────────────────────────────
    print("\n[4/4] Saving output...")
    save_chunks(chunks, output_path, args.source, args.input,
                kept_pages, total_pages, args.chunk_size, args.overlap)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  Saved       : {output_path}  ({size_kb:.1f} KB)")

    # ── Done ─────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  DONE")
    print(f"  Submit → {os.path.basename(output_path)} | {args.source} | {len(chunks)} chunks")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
