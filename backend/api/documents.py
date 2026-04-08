"""Document upload / ingestion API (stub — wire to pipeline later)."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["documents"])


@router.post("/api/upload")
async def upload_document() -> dict:
    return {
        "ok": False,
        "message": (
            "Upload pipeline not implemented yet. "
            "Add PDFs under data/raw, regenerate chunks, then run scripts/ingest_laws.py."
        ),
    }
