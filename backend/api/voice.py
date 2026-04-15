"""Voice endpoints (Whisper STT)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.core.auth_http import optional_bearer_token
from backend.core.config import get_settings
from backend.services.voice_stt import transcribe_audio_bytes

router = APIRouter(tags=["voice"])


@router.post("/api/voice/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: Literal["auto", "en", "bn"] = Form("auto"),
    token_payload: dict | None = Depends(optional_bearer_token),
) -> dict[str, str]:
    s = get_settings()
    if s.enforce_auth_chat and not token_payload:
        raise HTTPException(status_code=401, detail={"error": "authentication required"})
    if token_payload and str(token_payload.get("ver", "")) != "approved":
        raise HTTPException(status_code=403, detail={"error": "account not approved"})
    if not file.filename:
        raise HTTPException(status_code=400, detail={"error": "audio filename missing"})
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail={"error": "empty audio upload"})

    whisper_lang = None if language == "auto" else language
    try:
        text = transcribe_audio_bytes(
            filename=file.filename,
            audio_bytes=content,
            language=whisper_lang,
        )
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e
