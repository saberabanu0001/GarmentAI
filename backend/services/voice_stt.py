"""Speech-to-text via Whisper-compatible API."""

from __future__ import annotations

import io

from openai import OpenAI

from backend.core.config import get_settings


def _resolve_whisper_base_url() -> str | None:
    s = get_settings()
    if s.whisper_base_url:
        return s.whisper_base_url
    # If we are relying on Groq key and no explicit STT endpoint is set,
    # route to Groq's OpenAI-compatible base URL by default.
    if s.groq_api_key and not s.whisper_api_key:
        return "https://api.groq.com/openai/v1"
    return None


def transcribe_audio_bytes(
    *,
    filename: str,
    audio_bytes: bytes,
    language: str | None = None,
) -> str:
    """Transcribe audio bytes with Whisper model and return plain text."""
    s = get_settings()
    api_key = s.whisper_api_key or s.groq_api_key
    if not api_key:
        raise RuntimeError("Set WHISPER_API_KEY (or GROQ_API_KEY) in environment.")

    client = OpenAI(api_key=api_key, base_url=_resolve_whisper_base_url())

    f = io.BytesIO(audio_bytes)
    f.name = filename or "audio.webm"

    resp = client.audio.transcriptions.create(
        model=s.whisper_model,
        file=f,
        language=language,
    )
    text = str(getattr(resp, "text", "") or "").strip()
    if not text:
        raise RuntimeError("Whisper returned empty transcription.")
    return text
