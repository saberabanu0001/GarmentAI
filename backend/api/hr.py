"""HR-only endpoints: document library uploads."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from backend.core.auth_http import require_hr_staff
from backend.services import hr_documents
from backend.services import rag_cache


def _background_ingest_hr(doc_id: str) -> None:
    from backend.services import hr_chroma_ingest

    try:
        res = hr_chroma_ingest.ingest_hr_document_to_chroma(doc_id)
        hr_documents.set_chroma_ingest_status(
            doc_id,
            indexed=True,
            chunk_count=res["chunk_count"],
            error=None,
        )
    except Exception as e:
        hr_documents.set_chroma_ingest_status(
            doc_id,
            indexed=False,
            chunk_count=0,
            error=str(e),
        )


router = APIRouter(tags=["hr"])


class HrDocumentUpdateBody(BaseModel):
    category: str


@router.get("/api/hr/documents")
def hr_list_documents(_auth: Annotated[dict, Depends(require_hr_staff)]) -> dict:
    return {"documents": hr_documents.list_documents()}


@router.post("/api/hr/documents")
async def hr_upload_document(
    _auth: Annotated[dict, Depends(require_hr_staff)],
    background_tasks: BackgroundTasks,
    category: Annotated[str, Form()],
    language: Annotated[str, Form()] = "en",
    file: UploadFile = File(...),
) -> dict:
    content = await file.read()
    email = str(_auth.get("email", ""))
    try:
        row = hr_documents.add_document(
            category=category,
            original_filename=file.filename or "document",
            content=content,
            mime_type=file.content_type or "application/octet-stream",
            uploaded_by_email=email,
            language=language,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": str(e)}) from e
    background_tasks.add_task(_background_ingest_hr, str(row["id"]))
    rag_cache.clear_all()
    return {"ok": True, "document": row}


@router.post("/api/hr/documents/{doc_id}/ingest")
def hr_reingest_document(
    doc_id: str,
    _auth: Annotated[dict, Depends(require_hr_staff)],
    background_tasks: BackgroundTasks,
) -> dict:
    """Queue Chroma re-index for an existing upload (PDF/text)."""
    row = hr_documents.get_document_by_id(doc_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "document not found"})
    background_tasks.add_task(_background_ingest_hr, doc_id)
    rag_cache.clear_all()
    return {"ok": True, "queued": True, "document_id": doc_id}


@router.patch("/api/hr/documents/{doc_id}")
def hr_update_document(
    doc_id: str,
    body: HrDocumentUpdateBody,
    _auth: Annotated[dict, Depends(require_hr_staff)],
    background_tasks: BackgroundTasks,
) -> dict:
    try:
        row = hr_documents.update_document_category(doc_id, category=body.category)
    except ValueError as e:
        msg = str(e)
        code = 404 if "not found" in msg else 400
        raise HTTPException(status_code=code, detail={"error": msg}) from e
    background_tasks.add_task(_background_ingest_hr, doc_id)
    rag_cache.clear_all()
    return {"ok": True, "reindexed": True, "document": row}


@router.delete("/api/hr/documents/{doc_id}")
def hr_delete_document(
    doc_id: str,
    _auth: Annotated[dict, Depends(require_hr_staff)],
) -> dict:
    row = hr_documents.delete_document(doc_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "document not found"})
    from backend.services import hr_chroma_ingest

    hr_chroma_ingest.delete_hr_document_vectors(doc_id)
    rag_cache.clear_all()
    return {"ok": True, "deleted": True, "document_id": doc_id}
