"""
Shared preprocessing pipeline for document chunking.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter

import fitz  # PyMuPDF


def parse_args():
    parser = argparse.ArgumentParser(
        description="Preprocess a PDF into standardized, metadata-rich text chunks."
    )
    parser.add_argument("--input", required=True, help="Path to the input PDF file")
    parser.add_argument("--source", required=True, help="Short source label")
    parser.add_argument("--skip_first", type=int, default=0,
                        help="Number of pages to skip at the start")
    parser.add_argument("--skip_last", type=int, default=0,
                        help="Number of pages to skip at the end")
    parser.add_argument("--skip_ranges", nargs="*", default=[], metavar="START-END",
                        help="1-indexed page ranges to skip")
    parser.add_argument("--chunk_size", type=int, default=1000,
                        help="Target characters per chunk")
    parser.add_argument("--overlap", type=int, default=100,
                        help="Target overlap characters between chunks")
    parser.add_argument("--output_dir", default="processed",
                        help="Output directory")
    parser.add_argument("--output_name", default=None,
                        help="Optional output filename override")
    return parser.parse_args()


def build_skip_set(total_pages, skip_first, skip_last, skip_ranges):
    skip = set()
    skip.update(range(0, skip_first))
    skip.update(range(max(total_pages - skip_last, 0), total_pages))
    for page_range in skip_ranges:
        try:
            start, end = page_range.split("-")
            skip.update(range(int(start) - 1, int(end)))
        except ValueError:
            print(f"  Warning: could not parse skip range '{page_range}'")
    return skip


def normalize_line_for_frequency(line):
    line = re.sub(r"\d+", "#", line.strip())
    line = re.sub(r"\s+", " ", line)
    return line


def is_probable_noise_line(line):
    stripped = line.strip()
    if not stripped:
        return False
    if len(stripped) <= 2:
        return True
    # Date/Time patterns: 3/25/26, 9:25 AM or 2026-03-25 etc.
    if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{2,4},?\s*\d{1,2}:\d{2}\s*(AM|PM)?", stripped, flags=re.IGNORECASE):
        return True
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", stripped):
        return True
    if re.fullmatch(r"\d{1,2}:\d{2}\s*(AM|PM)", stripped, flags=re.IGNORECASE):
        return True
    # Page numbers
    if re.fullmatch(r"page\s*\d+(\s*of\s*\d+)?", stripped, flags=re.IGNORECASE):
        return True
    # Site noise
    if re.search(r"manualslib", stripped, flags=re.IGNORECASE):
        return True
    if stripped.lower() in ["contents", "table of contents", "index"]:
        return True
    return False


def collect_repeated_lines(page_entries):
    normalized_counts = Counter()
    raw_variants = {}

    for entry in page_entries:
        page_seen = set()
        for raw_line in entry["text"].splitlines():
            if not raw_line.strip():
                continue
            normalized = normalize_line_for_frequency(raw_line)
            if len(normalized) < 6:
                continue
            if normalized in page_seen:
                continue
            page_seen.add(normalized)
            normalized_counts[normalized] += 1
            raw_variants.setdefault(normalized, raw_line.strip())

    # A line is repeated if it appears on at least 15% of pages or at least 3 pages
    threshold = max(3, int(len(page_entries) * 0.15)) if page_entries else 3
    repeated = set()
    for normalized, count in normalized_counts.items():
        candidate = raw_variants[normalized]
        if count < threshold:
            continue
        
        # Always remove headers/footers that look like document titles or structural elements
        if re.search(r"(manual|labour act|fire safety|social compliance|module|version|compliance practices)",
                     candidate, flags=re.IGNORECASE):
            repeated.add(normalized)
            continue
        
        # Short all-caps lines are often headers
        if len(candidate.split()) <= 12 and candidate.upper() == candidate:
            repeated.add(normalized)
            
    return repeated


def clean_page_text(text, repeated_lines):
    text = text.replace("\x0c", "\n")
    # Remove URLs
    text = re.sub(r"(https?://|www\.)\S+", "", text)
    # Remove characters outside ASCII basic set
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    
    # Specific document banners identified by user
    text = re.sub(r"\bR\s+S\s+C\s+F\s+I\s+R\s+E\s+S\s+A\s+F\s+E\s+T\s+Y[^\n]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"RSC Fire Safety Manual for RMG Buildings[^\n]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Social Compliance\s*&\s*Environmental Management[^\n]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Skills for Industry Competitiveness and Innovation Program[^\n]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Journal of\s+Business\s+and\s+Technology[^\n]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Hossain\s*&\s*Rahman[^\n]*", "", text, flags=re.IGNORECASE)
    
    # Bangladesh Labour Act specific noise
    text = re.sub(r"THE\s+BANGLADESH\s+LABOUR\s+ACT,\s*2006", "Bangladesh Labour Act, 2006", text, flags=re.IGNORECASE)
    
    # Sewing Machine manual specific noise (ManualsLib etc.)
    text = re.sub(r"JUKI DU-\d+[^\n]*ManualsLib[^\n]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\d+/\d+/\d+,\s*\d+:\d+\s*(AM|PM)\s*JUKI DU-\d+[^\n]*", "", text, flags=re.IGNORECASE)

    # Separator lines
    text = re.sub(r"[-=_]{3,}", "", text)
    text = re.sub(r"\.{4,}", "", text)

    cleaned_lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            cleaned_lines.append("")
            continue

        normalized = normalize_line_for_frequency(line)
        if normalized in repeated_lines:
            continue
        if is_probable_noise_line(line):
            continue
        if re.fullmatch(r"\d{1,3}", line): # Lone page numbers
            continue

        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)
    # Cleanup whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # Fix broken hyphenation
    text = re.sub(r"(?<!\n)-\n(?=[a-z])", "", text)
    # Join lines that were broken in the middle of a sentence
    text = re.sub(r"(?<!\n)\n(?=[a-z])", " ", text)
    
    # Punctuation cleanup
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    
    return text.strip()


def extract_pages(pdf_path, skip_pages):
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    page_entries = []

    for index, page in enumerate(doc):
        if index in skip_pages:
            continue
        text = page.get_text()
        if text.strip():
            page_entries.append({
                "page_num": index + 1,
                "text": text,
            })

    doc.close()
    return page_entries, total_pages


def build_document_text(page_entries):
    repeated_lines = collect_repeated_lines(page_entries)
    parts = []
    page_ranges = []
    position = 0

    for entry in page_entries:
        cleaned = clean_page_text(entry["text"], repeated_lines)
        if not cleaned:
            continue
        if parts:
            separator = "\n\n"
            parts.append(separator)
            position += len(separator)

        start = position
        parts.append(cleaned)
        position += len(cleaned)
        end = position
        page_ranges.append((start, end, entry["page_num"]))

    return "".join(parts), page_ranges


def find_boundary(text, start, max_end, min_step):
    """Finds a clean break point (paragraph, sentence, or list item)."""
    search_start = min(max(start + max(min_step // 2, 1), start), max_end)
    
    # Priority 1: Paragraphs
    paragraph = text.rfind("\n\n", search_start, max_end)
    if paragraph > start:
        return paragraph

    # Priority 2: Sentence enders
    sentence_candidates = [
        text.rfind(marker, search_start, max_end)
        for marker in (". ", ".\n", "? ", "?\n", "! ", "!\n")
    ]
    sentence = max(sentence_candidates)
    if sentence > start:
        return sentence + 1

    # Priority 3: List items or newlines
    # Look for patterns like "\n(ii)" or "\n2."
    list_item = re.search(r"\n\s*(\([a-z0-9]+\)|\d+\.|[a-z]\.)\s+", text[search_start:max_end])
    if list_item:
        return search_start + list_item.start()

    newline = text.rfind("\n", search_start, max_end)
    if newline > start:
        return newline

    # Fallback to space
    space = text.rfind(" ", search_start, max_end)
    if space > start:
        return space
        
    return max_end


def align_chunk_start(text, desired_start, previous_end):
    """
    Slides the start point of a chunk to a clean boundary.
    Ensures we don't start in the middle of a word or sentence.
    """
    if desired_start <= 0:
        return 0

    limit = min(previous_end, len(text))
    # Look back a bit to find a better start point
    backward_floor = max(0, desired_start - 250)

    # Priority 1: Paragraph break
    backward_paragraph = text.rfind("\n\n", backward_floor, desired_start)
    if backward_paragraph != -1:
        candidate = backward_paragraph + 2
        if candidate < limit:
            return candidate

    # Priority 2: List item start
    # Look for "\n(i)" or "\n1." in the lookback window
    list_match = re.search(r"\n\s*(\([a-z0-9]+\)|\d+\.|[a-z]\.)\s+", text[backward_floor:desired_start])
    if list_match:
        candidate = backward_floor + list_match.start() + 1
        return candidate

    # Priority 3: Sentence boundary
    backward_sentence = max(
        text.rfind(". ", backward_floor, desired_start),
        text.rfind(".\n", backward_floor, desired_start),
        text.rfind("? ", backward_floor, desired_start),
        text.rfind("?\n", backward_floor, desired_start),
        text.rfind("! ", backward_floor, desired_start),
        text.rfind("!\n", backward_floor, desired_start),
    )
    if backward_sentence != -1:
        candidate = backward_sentence + 2
        if candidate < limit:
            return candidate

    # If no clean boundary found in lookback, look forward slightly
    forward_limit = min(desired_start + 100, limit)
    paragraph = text.find("\n\n", desired_start, forward_limit)
    if paragraph != -1:
        return paragraph + 2

    # Avoid breaking mid-word
    while desired_start < limit and text[desired_start].isalnum():
        desired_start += 1
    while desired_start < limit and text[desired_start].isspace():
        desired_start += 1
        
    return min(desired_start, limit)


def infer_section(chunk_text):
    for line in chunk_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if len(stripped) > 120:
            continue
        if re.match(r"^(\d+(\.\d+)*|chapter\s+[ivx0-9]+|section\s+\d+)\b", stripped,
                    flags=re.IGNORECASE):
            return stripped
        if stripped == stripped.upper() and len(stripped.split()) <= 12:
            return stripped
    first_line = chunk_text.strip().splitlines()[0].strip()
    return first_line[:80]


def page_span_for_range(page_ranges, start, end):
    pages = [page for range_start, range_end, page in page_ranges
             if range_end > start and range_start < end]
    if not pages:
        return None, None
    return min(pages), max(pages)


def chunk_text(text, page_ranges, chunk_size, overlap):
    chunks = []
    length = len(text)
    if length == 0:
        return chunks

    pos = 0
    min_step = max(chunk_size - overlap, 1)

    while pos < length:
        end = min(pos + chunk_size, length)
        if end >= length:
            chunk_start = pos
            chunk_end = length
        else:
            chunk_start = pos
            chunk_end = find_boundary(text, pos, end, min_step)

        chunk_text_value = text[chunk_start:chunk_end].strip()
        if chunk_text_value:
            page_start, page_end = page_span_for_range(page_ranges, chunk_start, chunk_end)
            chunks.append({
                "text": chunk_text_value,
                "start": chunk_start,
                "end": chunk_end,
                "page_start": page_start,
                "page_end": page_end,
                "section": infer_section(chunk_text_value),
            })

        if chunk_end >= length:
            break

        desired_start = max(chunk_end - overlap, 0)
        next_start = align_chunk_start(text, desired_start, chunk_end)
        if next_start <= pos:
            next_start = chunk_end
        pos = next_start

    return chunks


def save_chunks(chunks, output_path, source_name, pdf_path, kept_pages,
                total_pages, chunk_size, overlap):
    document_name = os.path.basename(pdf_path)
    source_label = source_name.lower().replace(" ", "_")
    
    with open(output_path, "w", encoding="utf-8") as handle:
        # Document-level header
        handle.write("=" * 80 + "\n")
        handle.write(f"DOCUMENT METADATA\n")
        handle.write(f"Source       : {source_name}\n")
        handle.write(f"File         : {document_name}\n")
        handle.write(f"Pages Kept   : {len(kept_pages)} of {total_pages}\n")
        handle.write(f"Chunk Count  : {len(chunks)}\n")
        handle.write(f"Target Size  : {chunk_size} chars\n")
        handle.write(f"Overlap      : {overlap} chars\n")
        handle.write("=" * 80 + "\n\n")

        for index, chunk in enumerate(chunks, 1):
            chunk_id = f"{source_label}__ch{index:04d}"
            
            # Per-chunk header with mandatory metadata
            handle.write(f"--- CHUNK {index} | ID: {chunk_id} | DOC: {document_name} | SOURCE: {source_name} | PAGE: {chunk['page_start']} to {chunk['page_end']} ---\n")
            if chunk.get('section'):
                handle.write(f"SECTION: {chunk['section']}\n")
            
            handle.write("\n")
            handle.write(f"{chunk['text']}\n")
            handle.write("\n" + "-" * 80 + "\n\n")


def run_pipeline(args):
    if not os.path.isfile(args.input):
        print(f"File not found: {args.input}")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", args.source).lower().strip("_")
    output_name = args.output_name or f"{safe_name}_chunks.txt"
    output_path = os.path.join(args.output_dir, output_name)

    print("=" * 60)
    print(f"  Source : {args.source}")
    print(f"  Input  : {args.input}")
    print(f"  Output : {output_path}")
    print("=" * 60)

    tmp_doc = fitz.open(args.input)
    total_pages = len(tmp_doc)
    tmp_doc.close()
    skip_pages = build_skip_set(total_pages, args.skip_first, args.skip_last, args.skip_ranges)

    print("\n[1/4] Extracting text...")
    page_entries, total_pages = extract_pages(args.input, skip_pages)
    kept_pages = [entry["page_num"] for entry in page_entries]
    raw_chars = sum(len(entry["text"]) for entry in page_entries)
    print(f"  Pages kept : {len(kept_pages)} / {total_pages}")
    print(f"  Raw chars  : {raw_chars:,}")

    print("\n[2/4] Cleaning text...")
    cleaned_text, page_ranges = build_document_text(page_entries)
    removed = raw_chars - len(cleaned_text)
    removed_pct = (removed / raw_chars * 100) if raw_chars else 0.0
    print(f"  Clean chars: {len(cleaned_text):,}  (removed {removed:,} = {removed_pct:.1f}%)")

    print("\n[3/4] Chunking...")
    chunks = chunk_text(cleaned_text, page_ranges, args.chunk_size, args.overlap)
    avg_len = sum(len(chunk["text"]) for chunk in chunks) // max(len(chunks), 1)
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Avg length  : {avg_len} chars")

    print("\n[4/4] Saving...")
    save_chunks(chunks, output_path, args.source, args.input, kept_pages,
                total_pages, args.chunk_size, args.overlap)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  Saved: {output_path}  ({size_kb:.1f} KB)")

    print("\n" + "=" * 60)
    print(f"  DONE -> {os.path.basename(output_path)} | {args.source} | {len(chunks)} chunks")
    print("=" * 60 + "\n")


def main():
    run_pipeline(parse_args())


if __name__ == "__main__":
    main()
