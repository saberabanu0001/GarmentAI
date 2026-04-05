#!/usr/bin/env python3
"""
Chunk markdown using LangChain RecursiveCharacterTextSplitter + custom
preprocessing and metadata (chapter/section propagation).

Outputs go to ../chunked-data/ by default (repo root).

Install (from repo root): pip install -r requirements.txt

Example (from repo root):
  python chunked-data-code/chunk_markdown_langchain.py \\
    --input "md data/labour_rules_full.md" \\
    --source-name "Labour Rules" \\
    --document-name "Labour Rules 2015"

Example (from this directory):
  python chunk_markdown_langchain.py \\
    --input "../md data/labour_rules_full.md" \\
    --source-name "Labour Rules"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

# Parent of chunked-data-code/ = repository root
REPO_ROOT = Path(__file__).resolve().parent.parent


def resolve_existing_file(path: Path) -> Path | None:
    """Return absolute path if file exists (cwd, then repo root)."""
    path = path.expanduser()
    if path.is_file():
        return path.resolve()
    candidate = REPO_ROOT / path
    if candidate.is_file():
        return candidate.resolve()
    return None


# PDF/Markdown export noise: repeated cover title on its own line.
_RUNNING_TITLE_LINE = re.compile(
    r"^Bangladesh\s+Labour\s+Act,\s*2006\s*$", re.IGNORECASE
)
# Standalone page numbers (1–3 digits) on their own line.
_PAGE_ONLY_LINE = re.compile(r"^\d{1,3}\s*$")


def strip_conversion_artifacts(
    text: str,
    *,
    strip_running_title: bool = True,
    strip_page_numbers: bool = True,
) -> str:
    """Remove common PDF-to-markdown junk without touching real legal text."""
    lines: list[str] = []
    running_title_kept = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append(line)
            continue
        if strip_running_title and _RUNNING_TITLE_LINE.match(stripped):
            if not running_title_kept:
                lines.append(line)
                running_title_kept = True
            continue
        if strip_page_numbers and _PAGE_ONLY_LINE.match(stripped):
            continue
        lines.append(line)
    return "\n".join(lines)


def preprocess_markdown(
    text: str,
    *,
    strip_running_title: bool = True,
    strip_page_numbers: bool = True,
) -> str:
    text = strip_conversion_artifacts(
        text,
        strip_running_title=strip_running_title,
        strip_page_numbers=strip_page_numbers,
    )
    text = re.sub(r"\n## \*\*CHAPTER", "\n\n## **CHAPTER", text)
    text = re.sub(r"\n(\d+)\.\s+\*\*", r"\n\n\1. **", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def extract_metadata_with_context(
    chunk_text: str, chunk_index: int, all_chunks: list[str]
) -> dict:
    metadata = {
        "chunk_id": chunk_index,
        "chapter": None,
        "chapter_number": None,
        "section": None,
        "section_number": None,
        "subsections": [],
        "word_count": len(chunk_text.split()),
        "char_count": len(chunk_text),
        "content_type": "unknown",
    }

    if chunk_index == 0 or "ACT NO." in chunk_text:
        metadata["content_type"] = "title_page"
    elif "CHAPTER" in chunk_text:
        metadata["content_type"] = "chapter_content"
    elif re.search(r"^\s*\d+\.\s+\*\*", chunk_text, re.MULTILINE):
        metadata["content_type"] = "section_content"
    else:
        metadata["content_type"] = "continuation"

    chapter_match = re.search(
        r"CHAPTER\s+([IVXLCDM]+)\s+(.+?)(?:\*\*|\n)", chunk_text
    )
    if chapter_match:
        metadata["chapter_number"] = chapter_match.group(1)
        metadata["chapter"] = (
            chapter_match.group(2).strip().rstrip("*").strip()
        )
    else:
        for i in range(chunk_index - 1, max(-1, chunk_index - 10), -1):
            if i >= 0:
                prev_match = re.search(
                    r"CHAPTER\s+([IVXLCDM]+)\s+(.+?)(?:\*\*|\n)",
                    all_chunks[i],
                )
                if prev_match:
                    metadata["chapter_number"] = prev_match.group(1)
                    metadata["chapter"] = (
                        prev_match.group(2).strip().rstrip("*").strip()
                    )
                    break

    section_pattern = re.compile(
        r"^\s*(\d+)\.\s+\*\*(.+?)\.\*\*", re.MULTILINE
    )
    section_match = section_pattern.search(chunk_text)
    if section_match:
        metadata["section_number"] = section_match.group(1)
        metadata["section"] = section_match.group(2).strip()
    else:
        for i in range(chunk_index - 1, max(-1, chunk_index - 10), -1):
            if i >= 0:
                prev_matches = list(section_pattern.finditer(all_chunks[i]))
                if prev_matches:
                    m = prev_matches[-1]
                    metadata["section_number"] = m.group(1)
                    metadata["section"] = m.group(2).strip()
                    break

    # Only markdown list markers like "- (a)" — not every "(a)" in prose.
    subsection_matches = re.findall(
        r"^\s*-\s*\(([a-z])\)", chunk_text, re.MULTILINE
    )
    if subsection_matches:
        metadata["subsections"] = list(dict.fromkeys(subsection_matches[:10]))

    return metadata


def build_section_line(meta: dict) -> str:
    parts = []
    if meta.get("chapter_number") and meta.get("chapter"):
        parts.append(
            f"Chapter {meta['chapter_number']}: {meta['chapter']}"
        )
    if meta.get("section_number") and meta.get("section"):
        parts.append(f"Section {meta['section_number']}: {meta['section']}")
    if parts:
        return " | ".join(parts)
    return meta.get("content_type") or "unknown"


def write_readme_format(
    out_path: Path,
    source_name: str,
    document_name: str,
    chunks: list[str],
    metas: list[dict],
) -> None:
    lines = [
        "DOCUMENT_METADATA",
        f"source_name: {source_name}",
        f"document_name: {document_name}",
        "",
    ]
    for i, (chunk, meta) in enumerate(zip(chunks, metas)):
        section = build_section_line(meta)
        lines.extend(
            [
                "--- CHUNK START ---",
                f"chunk_id: {i}",
                f"document_name: {document_name}",
                f"source_name: {source_name}",
                "page_start: n/a",
                "page_end: n/a",
                f"section: {section}",
                "text:",
                chunk,
                "--- CHUNK END ---",
                "",
            ]
        )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Chunk markdown with LangChain.")
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to .md file (relative to cwd or repo root)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "chunked-data",
        help="Directory for manifest, combined txt, and optional raw chunks",
    )
    parser.add_argument(
        "--source-name",
        required=True,
        help='Value for source_name (e.g. "Labour Rules")',
    )
    parser.add_argument(
        "--document-name",
        default=None,
        help="Defaults to input file stem if omitted",
    )
    parser.add_argument("--chunk-size", type=int, default=3500)
    parser.add_argument("--chunk-overlap", type=int, default=600)
    parser.add_argument("--min-chunk-chars", type=int, default=100)
    parser.add_argument(
        "--write-raw-chunks",
        action="store_true",
        help="Also write chunk_0.txt, chunk_1.txt, ... into output-dir",
    )
    parser.add_argument(
        "--keep-running-title",
        action="store_true",
        help="Keep repeated full-line 'Bangladesh Labour Act, 2006' lines.",
    )
    parser.add_argument(
        "--keep-page-numbers",
        action="store_true",
        help="Keep standalone 1–3 digit lines (PDF page numbers).",
    )
    args = parser.parse_args()

    in_path = resolve_existing_file(args.input)
    if in_path is None:
        print(f"Error: input not found: {args.input}", file=sys.stderr)
        return 1

    document_name = args.document_name or in_path.stem
    text = in_path.read_text(encoding="utf-8")
    text = preprocess_markdown(
        text,
        strip_running_title=not args.keep_running_title,
        strip_page_numbers=not args.keep_page_numbers,
    )
    print(f"Original (after preprocess): {len(text)} chars\n")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        separators=[
            "\n\n## **CHAPTER",
            "\n\n## ",
            "\n### ",
            "\n\n\n",
            "\n\n",
            "\n- (",
            "\n   - ",
            "\n- ",
            "\n",
            ". ",
            " ",
            "",
        ],
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    chunks = [c for c in chunks if len(c) >= args.min_chunk_chars]

    if not chunks:
        print("No chunks produced (check min-chunk-chars and input).", file=sys.stderr)
        return 1

    out_dir = args.output_dir
    if not out_dir.is_absolute():
        out_dir = (REPO_ROOT / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    metas: list[dict] = []
    chunk_data: list[dict] = []
    for i, chunk in enumerate(chunks):
        meta = extract_metadata_with_context(chunk, i, chunks)
        metas.append(meta)
        summary_parts = []
        if meta["chapter"]:
            summary_parts.append(f"Ch.{meta['chapter_number']}")
        if meta["section"]:
            summary_parts.append(f"Sec.{meta['section_number']}")
        if meta["subsections"]:
            summary_parts.append(f"{len(meta['subsections'])} subsections")
        summary = " | ".join(summary_parts) if summary_parts else meta["content_type"]
        chunk_data.append(
            {
                "chunk_id": i,
                "file": f"chunk_{i}.txt",
                "metadata": meta,
                "summary": summary,
                "preview": chunk[:200].replace("\n", " ").strip() + "...",
            }
        )
        print(
            f"Chunk {i:3d} | {meta['char_count']:4d} chars | "
            f"{meta['content_type']:15s} | {summary}"
        )

        if args.write_raw_chunks:
            (out_dir / f"chunk_{i}.txt").write_text(chunk, encoding="utf-8")

    stem = re.sub(r"[^\w\-]+", "_", document_name).strip("_") or "document"
    combined_path = out_dir / f"{stem}_chunks.txt"
    write_readme_format(
        combined_path, args.source_name, document_name, chunks, metas
    )

    total_chars = sum(len(c) for c in chunks)
    manifest = {
        "document_info": {
            "source_file": str(in_path),
            "total_chunks": len(chunks),
            "avg_chunk_size": total_chars // len(chunks),
        },
        "chunking_config": {
            "chunk_size": args.chunk_size,
            "chunk_overlap": args.chunk_overlap,
            "min_chunk_size": args.min_chunk_chars,
        },
        "chunks": chunk_data,
    }
    manifest_path = out_dir / f"{stem}_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\n" + "=" * 80)
    print("FINAL QUALITY REPORT")
    print("=" * 80)
    content_types: dict[str, int] = {}
    for item in chunk_data:
        ct = item["metadata"]["content_type"]
        content_types[ct] = content_types.get(ct, 0) + 1
    print("\nContent distribution:")
    n = len(chunks)
    for ctype, count in sorted(content_types.items()):
        pct = count * 100 // n
        print(f"  {ctype:20s}: {count:3d} chunks ({pct}%)")
    chunks_with_chapter = sum(1 for c in chunk_data if c["metadata"]["chapter"])
    chunks_with_section = sum(1 for c in chunk_data if c["metadata"]["section"])
    print("\nMetadata coverage:")
    print(
        f"  Chapter info: {chunks_with_chapter}/{n} "
        f"({chunks_with_chapter * 100 // n}%)"
    )
    print(
        f"  Section info: {chunks_with_section}/{n} "
        f"({chunks_with_section * 100 // n}%)"
    )
    sizes = [len(c) for c in chunks]
    print("\nSize stats:")
    print(f"  Min: {min(sizes)} chars")
    print(f"  Max: {max(sizes)} chars")
    print(f"  Avg: {sum(sizes) // len(sizes)} chars")
    print(f"\nWrote: {combined_path}")
    print(f"Wrote: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
