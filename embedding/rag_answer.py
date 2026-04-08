"""Compatibility shim."""

from backend.services.chroma_engine import ChromaHit
from backend.services.rag import rag_answer

__all__ = ["rag_answer", "ChromaHit"]
