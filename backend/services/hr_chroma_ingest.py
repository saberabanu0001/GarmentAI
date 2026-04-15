"""Ingest HR-uploaded PDFs into Chroma: extract text, chunk, E5 embed, upsert."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chromadb
import numpy as np
import pymupdf4llm
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.core.config import get_settings
from backend.services.embedder import E5Embedder

DEFAULT_MODEL = "intfloat/multilingual-e5-small"
HR_UPLOADS_COLLECTION = "hr_uploads"


def _allowed_roles_csv_for_category(category: str) -> str:
    c = (category or "other").lower()
    if c in ("training", "compliance"):
        return "worker,supervisor,compliance_officer,hr_staff"
    return "hr_staff,compliance_officer"


def _ensure_chroma_meta(persist_dir: Path) -> None:
    persist_dir.mkdir(parents=True, exist_ok=True)
    meta_path = persist_dir / "meta.json"
    if meta_path.is_file():
        return
    meta_path.write_text(
        json.dumps(
            {
                "model": DEFAULT_MODEL,
                "built_at": datetime.now(timezone.utc).isoformat(),
                "chunks_dir": "",
                "manifest": "",
                "collections": {},
                "normalize_embeddings": True,
                "passage_prefix": "passage: ",
                "query_prefix": "query: ",
                "note": "Bootstrapped for HR uploads; run scripts/ingest_laws.py for full corpus.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def extract_text_from_pdf(path: Path) -> str:
    md = pymupdf4llm.to_markdown(str(path))
    text = (md or "").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def extract_text_from_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip()


def chunk_plain_text(text: str, *, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    if not text:
        return []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
    )
    return splitter.split_text(text)


def ingest_hr_document_to_chroma(doc_id: str) -> dict[str, Any]:
    """
    Load document row by id from HR index, extract text, chunk, embed, upsert into Chroma.
    Deletes prior chunks for this doc_id in hr_uploads.
    Returns {"chunk_count": int, "collection": str}.
    """
    s = get_settings()
    from backend.services import hr_documents as hr_doc_mod

    row = hr_doc_mod.get_document_by_id(doc_id)
    if row is None:
        raise ValueError("document not found in index")

    rel = str(row.get("rel_path", ""))
    if not rel:
        raise ValueError("missing rel_path")

    path = s.hr_uploads_dir / rel
    if not path.is_file():
        raise FileNotFoundError(f"missing file: {path}")

    mime = str(row.get("mime_type", "")).lower()
    category = str(row.get("category", "other"))
    language = str(row.get("language", "en")).lower()
    if language not in ("en", "bn"):
        language = "en"

    if mime == "application/pdf" or path.suffix.lower() == ".pdf":
        text = extract_text_from_pdf(path)
    elif mime.startswith("text/") or path.suffix.lower() in (".txt", ".md"):
        text = extract_text_from_txt(path)
    else:
        raise ValueError(
            f"auto-index supports PDF and plain text only (got {mime or path.suffix})"
        )

    chunks = chunk_plain_text(text)
    if not chunks:
        raise ValueError("no text extracted or empty after chunking")

    persist_dir = s.chroma_dir
    _ensure_chroma_meta(persist_dir)

    client = chromadb.PersistentClient(path=str(persist_dir))
    try:
        col = client.get_collection(HR_UPLOADS_COLLECTION)
    except Exception:
        col = client.create_collection(
            name=HR_UPLOADS_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

    try:
        col.delete(where={"hr_doc_id": doc_id})
    except Exception:
        pass

    embedder = E5Embedder(DEFAULT_MODEL)
    emb = embedder.encode(chunks, is_query=False, batch_size=8)

    allowed = _allowed_roles_csv_for_category(category)
    orig_name = str(row.get("original_filename", path.name))
    chunks_key = f"hr_upload/{doc_id}/{orig_name}"

    ids: list[str] = []
    embeddings: list[list[float]] = []
    documents: list[str] = []
    metadatas: list[dict[str, str | int | float | bool]] = []

    for i, (piece, row_emb) in enumerate(zip(chunks, emb, strict=True)):
        uid = f"hr_doc_{doc_id}_c{i}"
        ids.append(uid)
        embeddings.append(row_emb.astype(np.float32).tolist())
        documents.append(piece)
        metadatas.append(
            {
                "chunk_uid": uid,
                "chunk_id": i,
                "chunks_file": chunks_key,
                "document_name": orig_name,
                "source_name": "HR document upload",
                "section": "",
                "page_start": 0,
                "page_end": 0,
                "doc_scope": "tenant",
                "doc_category": category,
                "language": language,
                "factory_id": "",
                "allowed_roles": allowed,
                "collection": HR_UPLOADS_COLLECTION,
                "hr_doc_id": doc_id,
            }
        )

    col.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    return {"chunk_count": len(ids), "collection": HR_UPLOADS_COLLECTION}


def delete_hr_document_vectors(doc_id: str) -> None:
    """Best-effort removal of all vectors belonging to one HR document."""
    s = get_settings()
    client = chromadb.PersistentClient(path=str(s.chroma_dir))
    try:
        col = client.get_collection(HR_UPLOADS_COLLECTION)
    except Exception:
        return
    try:
        col.delete(where={"hr_doc_id": doc_id})
    except Exception:
        return
