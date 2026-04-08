"""RAG: Chroma retrieval + LLM answer."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from backend.core.config import get_settings
from backend.core.security import Role
from backend.services.chroma_engine import ChromaHit, ChromaQueryEngine
from backend.services.llm_wrapper import BackendName, chat


def _format_context(hits: list[ChromaHit]) -> str:
    blocks: list[str] = []
    for h in hits:
        header = f"[{h.rank}] {h.collection} | {h.source_name} | {h.section}"
        blocks.append(f"{header}\n{h.text.strip()}")
    return "\n\n---\n\n".join(blocks)


def _system_prompt(*, audience_worker_simple: bool) -> str:
    base = (
        "You are GarmentAI, a factory knowledge assistant. "
        "Use ONLY the CONTEXT below to answer. If the answer is not in the CONTEXT, say clearly "
        "that it is not in the provided excerpts (do not invent law or policy). "
        "Quote or paraphrase briefly; keep answers concise."
    )
    if audience_worker_simple:
        base += (
            " If the user's question is in Bengali, answer in simple, plain Bengali. "
            "If the question is in English, answer in English."
        )
    return base


def _resolve_backend(explicit: BackendName | None) -> BackendName:
    if explicit is not None:
        return explicit
    raw = (
        get_settings().llm_backend
        or os.environ.get("LLM_BACKEND", "ollama")
    ).strip().lower()
    if raw == "groq":
        return "groq"
    if raw == "gemini":
        return "gemini"
    return "ollama"


def rag_answer(
    question: str,
    *,
    role: Role,
    factory_id: str = "",
    top_k: int = 5,
    backend: BackendName | None = None,
    chroma_dir: Path | None = None,
    audience_worker_simple: bool = True,
) -> tuple[str, list[ChromaHit]]:
    """Returns (assistant_reply, hits_used)."""
    b = _resolve_backend(backend)

    print(
        "(RAG) Loading retriever; first call loads E5 then searches Chroma…",
        file=sys.stderr,
        flush=True,
    )
    engine = ChromaQueryEngine(chroma_dir) if chroma_dir else ChromaQueryEngine()
    hits = engine.search(question, role=role, factory_id=factory_id, top_k=top_k)
    _llm_hint = (
        "local Ollama may take 1–3+ min on CPU"
        if b == "ollama"
        else ("Gemini API" if b == "gemini" else "Groq is usually a few seconds")
    )
    print(
        f"(RAG) Retrieved {len(hits)} chunk(s); calling {b} ({_llm_hint})…",
        file=sys.stderr,
        flush=True,
    )
    ctx = _format_context(hits) if hits else "(no retrieved chunks)"
    system = _system_prompt(audience_worker_simple=audience_worker_simple)
    user = f"CONTEXT:\n{ctx}\n\nUSER QUESTION:\n{question.strip()}"
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    reply = chat(messages, backend=b)
    return reply.strip(), hits
