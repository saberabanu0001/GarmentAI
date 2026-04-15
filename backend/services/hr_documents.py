"""HR document uploads: files on disk + JSON index (DB migration later)."""

from __future__ import annotations

import json
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from backend.core.config import get_settings

HrDocCategory = Literal[
    "employee",
    "recruitment",
    "training",
    "compliance",
    "performance",
    "other",
]
HrDocLanguage = Literal["en", "bn"]

_VALID_CATEGORIES: frozenset[str] = frozenset(
    ("employee", "recruitment", "training", "compliance", "performance", "other"),
)
_VALID_LANGUAGES: frozenset[str] = frozenset(("en", "bn"))
_MAX_BYTES = 20 * 1024 * 1024
_INDEX_LOCK = threading.Lock()


def _safe_filename(name: str) -> str:
    base = Path(name).name
    base = re.sub(r"[^a-zA-Z0-9._-]", "_", base)[:180]
    return base or "upload.bin"


def _load_index(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"documents": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"documents": []}
    if not isinstance(data, dict) or not isinstance(data.get("documents"), list):
        return {"documents": []}
    return data


def _save_index(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_document_by_id(doc_id: str) -> dict[str, Any] | None:
    path = get_settings().hr_documents_index_path
    with _INDEX_LOCK:
        for item in _load_index(path)["documents"]:
            if isinstance(item, dict) and str(item.get("id")) == doc_id:
                return item
    return None


def set_chroma_ingest_status(
    doc_id: str,
    *,
    indexed: bool,
    chunk_count: int = 0,
    error: str | None = None,
) -> None:
    path = get_settings().hr_documents_index_path
    with _INDEX_LOCK:
        data = _load_index(path)
        for item in data["documents"]:
            if isinstance(item, dict) and str(item.get("id")) == doc_id:
                item["chroma_indexed"] = indexed
                item["chroma_chunks"] = int(chunk_count)
                item["chroma_error"] = error
                item["chroma_indexed_at"] = (
                    datetime.now(timezone.utc).isoformat() if indexed else None
                )
                break
        _save_index(path, data)


def list_documents() -> list[dict[str, Any]]:
    path = get_settings().hr_documents_index_path
    with _INDEX_LOCK:
        docs = _load_index(path)["documents"]
    out: list[dict[str, Any]] = []
    for item in docs:
        if isinstance(item, dict) and "id" in item:
            out.append(item)
    out.sort(key=lambda x: str(x.get("uploaded_at", "")), reverse=True)
    return out


def add_document(
    *,
    category: str,
    original_filename: str,
    content: bytes,
    mime_type: str,
    uploaded_by_email: str,
    language: str = "en",
) -> dict[str, Any]:
    language = (language or "en").strip().lower()
    if category not in _VALID_CATEGORIES:
        raise ValueError(f"invalid category: {category}")
    if language not in _VALID_LANGUAGES:
        raise ValueError(f"invalid language: {language}")
    if not content:
        raise ValueError("empty file")
    if len(content) > _MAX_BYTES:
        raise ValueError(f"file too large (max {_MAX_BYTES // (1024 * 1024)}MB)")

    s = get_settings()
    idx_path = s.hr_documents_index_path
    uid = str(uuid.uuid4())
    safe = _safe_filename(original_filename)
    rel = f"{uid}/{safe}"
    dest = s.hr_uploads_dir / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)

    row = {
        "id": uid,
        "category": category,
        "original_filename": original_filename,
        "mime_type": mime_type or "application/octet-stream",
        "size_bytes": len(content),
        "rel_path": rel.replace("\\", "/"),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": uploaded_by_email,
        "language": language,
        "chroma_indexed": False,
        "chroma_chunks": 0,
        "chroma_error": None,
        "chroma_indexed_at": None,
    }
    with _INDEX_LOCK:
        data = _load_index(idx_path)
        data["documents"].append(row)
        _save_index(idx_path, data)
    return row


def update_document_category(doc_id: str, *, category: str) -> dict[str, Any]:
    if category not in _VALID_CATEGORIES:
        raise ValueError(f"invalid category: {category}")

    path = get_settings().hr_documents_index_path
    with _INDEX_LOCK:
        data = _load_index(path)
        for item in data["documents"]:
            if isinstance(item, dict) and str(item.get("id")) == doc_id:
                item["category"] = category
                # Category changes can change role visibility; force re-index.
                item["chroma_indexed"] = False
                item["chroma_chunks"] = 0
                item["chroma_error"] = None
                item["chroma_indexed_at"] = None
                _save_index(path, data)
                return item
    raise ValueError("document not found")


def delete_document(doc_id: str) -> dict[str, Any] | None:
    """Delete index row and file from disk. Returns deleted row if found."""
    s = get_settings()
    idx_path = s.hr_documents_index_path
    with _INDEX_LOCK:
        data = _load_index(idx_path)
        docs = data["documents"]
        for i, item in enumerate(docs):
            if isinstance(item, dict) and str(item.get("id")) == doc_id:
                row = item
                rel = str(row.get("rel_path", ""))
                if rel:
                    try:
                        path = s.hr_uploads_dir / rel
                        if path.is_file():
                            path.unlink()
                        parent = path.parent
                        if parent.is_dir():
                            try:
                                next(parent.iterdir())
                            except StopIteration:
                                parent.rmdir()
                    except OSError:
                        pass
                docs.pop(i)
                _save_index(idx_path, data)
                return row
    return None
