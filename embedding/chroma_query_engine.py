"""Compatibility shim — prefer `backend.services.chroma_engine`."""

from backend.core.config import get_settings
from backend.services.chroma_engine import (
    ChromaHit,
    ChromaQueryEngine,
    collection_names_for_factory,
    main,
)

DEFAULT_CHROMA_DIR = get_settings().chroma_dir

__all__ = [
    "ChromaHit",
    "ChromaQueryEngine",
    "DEFAULT_CHROMA_DIR",
    "collection_names_for_factory",
    "main",
]

if __name__ == "__main__":
    raise SystemExit(main())
