"""Compatibility shim."""

from backend.services.parse_chunks import (
    CHUNK_BLOCK,
    ChunkRecord,
    load_all_chunks,
    parse_chunks_file,
    passage_for_embedding,
)

__all__ = [
    "CHUNK_BLOCK",
    "ChunkRecord",
    "load_all_chunks",
    "parse_chunks_file",
    "passage_for_embedding",
]
