"""
preprocess.py – General-purpose data preprocessing pipeline
============================================================
Workflow: Document → Text Extraction → Cleaning → Chunking → Save

Usage (run from Experiment/ folder):
    python scripts/preprocess.py --input raw/myfile.pdf --source "Source Name"
    python scripts/preprocess.py --input raw/myfile.pdf --source "Fire Safety" --skip_first 3 --skip_last 1 --skip_ranges 26-42
"""

import re
import os
import sys
import argparse
import fitz  # PyMuPDF


def parse_args():
    parser = argparse.ArgumentParser(
        description="Preprocess a PDF into clean text chunks for a knowledge base."
    )
    parser.add_argument("--input", required=True, help="Path to the input PDF file")
    parser.add_argument("--source", required=True, help="Short name for this data source")
    parser.add_argument("--skip_first", type=int, default=0,
                        help="Number of pages to skip at the START (cover, TOC). Default: 0")
    parser.add_argument("--skip_last", type=int, default=0,
                        help="Number of pages to skip at the END (colophon). Default: 0")
    parser.add_argument("--skip_ranges", nargs="*", default=[], metavar="START-END",
                        help="Page ranges to skip (1-indexed). E.g. --skip_ranges 26-42")
    parser.add_argument("--chunk_size", type=int, default=1000,
                        help="Target characters per chunk. Default: 1000")
    parser.add_argument("--overlap", type=int, default=100,
                        help="Overlap characters between chunks. Default: 100")
    parser.add_argument("--output_dir", default="processed",
                        help="Output directory. Default: processed/")
    return parser.parse_args()


def build_skip_set(total_pages, skip_first, skip_last, skip_ranges):
    skip = set()
    skip.update(range(0, skip_first))
    skip.update(range(total_pages - skip_last, total_pages))
    for r in skip_ranges:
        try:
            a, b = r.split("-")
            skip.update(range(int(a) - 1, int(b)))
        except ValueError:
            print(f"  ⚠ Could not parse skip range: '{r}'")
    return skip


def extract_text(pdf_path, skip_pages):
    doc = fitz.open(pdf_path)
    total = len(doc)
    parts, kept = [], []
    for i, page in enumerate(doc):
        if i in skip_pages:
            continue
        text = page.get_text()
        if text.strip():
            parts.append(text)
            kept.append(i + 1)
    doc.close()
    return "\n".join(parts), total, kept


def clean_text(text):
    text = re.sub(r'\b([A-Z])\s+([A-Z])\s+([A-Z])\s+([A-Z])\b[^\n]*\n?', '', text)
    text = re.sub(r'^\s*\d{1,3}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'Page\s+\d+\s*(of\s+\d+)?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(https?://|www\.)\S+', '', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'[-=_]{3,}', '', text)
    text = re.sub(r'\.{4,}', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = [ln for ln in text.split('\n') if len(ln.strip()) >= 3 or ln.strip() == '']
    return '\n'.join(lines).strip()


def chunk_text(text, chunk_size, overlap):
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
        sent = max(text.rfind('. ', search_start, end),
                   text.rfind('.\n', search_start, end))
        nl   = text.rfind('\n', search_start, end)

        if para > 0:     boundary = para
        elif sent > 0:   boundary = sent + 1
        elif nl > 0:     boundary = nl
        else:            boundary = end

        chunk = text[pos:boundary].strip()
        if chunk:
            chunks.append(chunk)

        pos = boundary - overlap
        if pos <= 0:
            pos = boundary

    return chunks


def save_chunks(chunks, output_path, source_name, pdf_path,
                kept_pages, total_pages, chunk_size, overlap):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"SOURCE  : {source_name}\n")
        f.write(f"FILE    : {os.path.basename(pdf_path)}\n")
        f.write(f"PAGES   : {len(kept_pages)} kept of {total_pages} total\n")
        f.write(f"CHUNKS  : {len(chunks)}  | Size: {chunk_size}  | Overlap: {overlap}\n")
        f.write("=" * 60 + "\n\n")
        for i, chunk in enumerate(chunks, 1):
            f.write(f"[CHUNK {i}]\n{chunk}\n\n")


def main():
    args = parse_args()

    if not os.path.isfile(args.input):
        print(f"❌ File not found: {args.input}")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    safe_name = re.sub(r'[^a-zA-Z0-9]+', '_', args.source).lower().strip('_')
    output_path = os.path.join(args.output_dir, f"{safe_name}_chunks.txt")

    print("=" * 60)
    print(f"  Source : {args.source}")
    print(f"  Input  : {args.input}")
    print(f"  Output : {output_path}")
    print("=" * 60)

    # Get total pages for skip_last calculation
    tmp = fitz.open(args.input)
    total_pages = len(tmp)
    tmp.close()

    skip_pages = build_skip_set(total_pages, args.skip_first, args.skip_last, args.skip_ranges)

    print("\n[1/4] Extracting text...")
    raw_text, total_pages, kept_pages = extract_text(args.input, skip_pages)
    print(f"  Pages kept : {len(kept_pages)} / {total_pages}")
    print(f"  Raw chars  : {len(raw_text):,}")

    print("\n[2/4] Cleaning text...")
    cleaned = clean_text(raw_text)
    removed = len(raw_text) - len(cleaned)
    print(f"  Clean chars: {len(cleaned):,}  (removed {removed:,} = {removed/len(raw_text)*100:.1f}%)")

    print("\n[3/4] Chunking...")
    chunks = chunk_text(cleaned, args.chunk_size, args.overlap)
    avg = sum(len(c) for c in chunks) // max(len(chunks), 1)
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Avg length  : {avg} chars")

    print("\n[4/4] Saving...")
    save_chunks(chunks, output_path, args.source, args.input,
                kept_pages, total_pages, args.chunk_size, args.overlap)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  Saved: {output_path}  ({size_kb:.1f} KB)")

    print("\n" + "=" * 60)
    print(f"  DONE → {os.path.basename(output_path)} | {args.source} | {len(chunks)} chunks")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
