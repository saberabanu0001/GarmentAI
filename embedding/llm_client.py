"""Compatibility shim — use `backend.services.llm_wrapper`."""

from backend.services.llm_wrapper import (
    BackendName,
    ChatMessage,
    chat,
    gemini_chat,
    groq_chat,
    ollama_chat,
)

__all__ = [
    "BackendName",
    "ChatMessage",
    "chat",
    "gemini_chat",
    "groq_chat",
    "ollama_chat",
]
