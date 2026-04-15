"""RAG chat endpoints: POST /api/chat and legacy POST /api/rag."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.core.auth_http import optional_bearer_token
from backend.core.config import get_settings
from backend.core.security import Role
from backend.services.llm_wrapper import BackendName
from backend.services.rag_budget import QuotaExceededError
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


def _resolve_chat_role(body: RagRequest, token_payload: dict | None) -> Role:
    s = get_settings()
    if token_payload is not None:
        if str(token_payload.get("ver", "")) != "approved":
            raise HTTPException(status_code=403, detail={"error": "account not approved"})
        try:
            return Role(str(token_payload.get("role", "")))
        except ValueError:
            raise HTTPException(
                status_code=403,
                detail={"error": "invalid token role"},
            ) from None
    if s.enforce_auth_chat:
        raise HTTPException(status_code=401, detail={"error": "authentication required"})
    try:
        return Role(body.role)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid role",
                "allowed": [r.value for r in Role if r is not Role.ALL],
            },
        ) from None


def _do_rag(body: RagRequest, token_payload: dict | None) -> RagResponse:
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question is required")
    role = _resolve_chat_role(body, token_payload)
    requester_key = ""
    if token_payload is not None:
        requester_key = str(token_payload.get("email") or token_payload.get("sub") or "").strip()
    if not requester_key:
        requester_key = f"anon:{role.value}"
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
            requester_key=requester_key,
        )
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "quota_exceeded",
                "message": str(e),
                "retry_after_seconds": e.retry_after_seconds,
            },
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e
    return RagResponse(answer=reply, hits=[h.to_dict() for h in hits])


@router.post("/api/chat", response_model=RagResponse)
def post_chat(
    body: RagRequest,
    token_payload: dict | None = Depends(optional_bearer_token),
) -> RagResponse:
    return _do_rag(body, token_payload)


@router.post("/api/rag", response_model=RagResponse)
def post_rag_compat(
    body: RagRequest,
    token_payload: dict | None = Depends(optional_bearer_token),
) -> RagResponse:
    """Backward-compatible alias for older clients."""
    return _do_rag(body, token_payload)
