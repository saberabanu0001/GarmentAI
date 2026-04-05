"""Parse combined *_chunks.txt files (README output contract)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


CHUNK_BLOCK = re.compile(
    r"--- CHUNK START ---\n"
    r"chunk_id: (\d+)\n"
    r"document_name: (.*?)\n"
    r"source_name: (.*?)\n"
    r"page_start: (.*?)\n"
    r"page_end: (.*?)\n"
    r"section: (.*?)\n"
    r"text:\n"
    r"(.*?)\n--- CHUNK END ---",
    re.DOTALL,
)


@dataclass
class ChunkRecord:
    chunk_id: int
    document_name: str
    source_name: str
    page_start: str
    page_end: str
    section: str
    text: str
    chunks_filename: str


def parse_chunks_file(path: Path) -> list[ChunkRecord]:
    raw = path.read_text(encoding="utf-8")
    out: list[ChunkRecord] = []
    for m in CHUNK_BLOCK.finditer(raw):
        out.append(
            ChunkRecord(
                chunk_id=int(m.group(1)),
                document_name=m.group(2).strip(),
                source_name=m.group(3).strip(),
                page_start=m.group(4).strip(),
                page_end=m.group(5).strip(),
                section=m.group(6).strip(),
                text=m.group(7).strip(),
                chunks_filename=path.name,
            )
        )
    return out


def load_all_chunks(chunks_dir: Path) -> list[ChunkRecord]:
    paths = sorted(chunks_dir.glob("*_chunks.txt"))
    all_rows: list[ChunkRecord] = []
    for p in paths:
        all_rows.extend(parse_chunks_file(p))
    return all_rows


def passage_for_embedding(rec: ChunkRecord) -> str:
    """Body only; E5Embedder adds the ``passage: `` prefix."""
    header = f"{rec.source_name} | {rec.document_name} | {rec.section}"
    return f"{header}\n\n{rec.text}"
