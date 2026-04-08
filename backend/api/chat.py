"""RAG chat endpoints: POST /api/chat and legacy POST /api/rag."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.core.security import Role
from backend.services.llm_wrapper import BackendName
from backend.services.rag import rag_answer

router = APIRouter(tags=["chat"])


class RagRequest(BaseModel):
    question: str = Field(..., min_length=1)
    role: str = "worker"
    factory_id: str = ""
    top_k: int = Field(default=5, ge=1, le=20)
    backend: Literal["groq"] | None = None
    response_language: Literal["auto", "en", "bn"] = "auto"


class RagResponse(BaseModel):
    answer: str
    hits: list[dict]


def _do_rag(body: RagRequest) -> RagResponse:
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question is required")
    try:
        role = Role(body.role)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid role",
                "allowed": [r.value for r in Role if r is not Role.ALL],
            },
        ) from None
    backend_choice: BackendName | None = body.backend
    try:
        reply, hits = rag_answer(
            question,
            role=role,
            factory_id=body.factory_id,
            top_k=body.top_k,
            backend=backend_choice,
            audience_worker_simple=(role is Role.WORKER),
            forced_language=body.response_language,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e
    return RagResponse(answer=reply, hits=[h.to_dict() for h in hits])


@router.post("/api/chat", response_model=RagResponse)
def post_chat(body: RagRequest) -> RagResponse:
    return _do_rag(body)


@router.post("/api/rag", response_model=RagResponse)
def post_rag_compat(body: RagRequest) -> RagResponse:
    """Backward-compatible alias for older clients."""
    return _do_rag(body)
