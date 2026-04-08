"""RAG: Chroma retrieval + LLM answer."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Literal

from backend.core.config import get_settings
from backend.core.security import Role
from backend.services.chroma_engine import ChromaHit, ChromaQueryEngine
from backend.services.llm_wrapper import BackendName, chat
from backend.services.rag_intent import greeting_reply, is_greeting_or_meta

# Cosine similarity from Chroma (higher = closer). Below this, we do not trust chunks for display or context.
_DEFAULT_MIN_SIM = 0.52


def _format_context(hits: list[ChromaHit]) -> str:
    blocks: list[str] = []
    for h in hits:
        header = f"[{h.rank}] {h.collection} | {h.source_name} | {h.section}"
        blocks.append(f"{header}\n{h.text.strip()}")
    return "\n\n---\n\n".join(blocks)


def _system_prompt(*, audience_worker_simple: bool, forced_language: Literal["auto", "en", "bn"] = "auto") -> str:
    base = (
        "You are GarmentAI, a supportive assistant for garment-factory workers. "
        "Use ONLY the CONTEXT excerpts below. If something is not in the CONTEXT, say honestly that "
        "this detail was not found in the materials you have (do not invent rules or numbers). "
        "Write in a warm, clear, human way—like a trusted colleague explaining their rights, not "
        "like a legal robot or a search-engine snippet. "
        "Prefer short paragraphs or a few bullet points when listing rights or steps. "
        "Do NOT mention 'context', 'retrieval', 'chunks', 'embeddings', or 'similarity scores'. "
        "Do NOT add a 'Sources' or 'References' section in your reply; the app shows document "
        "titles separately."
    )
    base += _language_instruction(
        audience_worker_simple=audience_worker_simple,
        forced_language=forced_language,
    )
    return base


def _resolve_backend(explicit: BackendName | None) -> BackendName:
    # Project decision: only Groq is enabled for generation.
    if explicit is not None and explicit != "groq":
        raise ValueError("Only backend=groq is enabled in this deployment")
    raw = (
        get_settings().llm_backend
        or os.environ.get("LLM_BACKEND", "groq")
    ).strip().lower()
    if raw != "groq":
        print(f"(RAG) Ignoring LLM_BACKEND={raw!r}; forcing groq.", file=sys.stderr, flush=True)
    return "groq"


def _min_similarity() -> float:
    try:
        return float(os.environ.get("RAG_MIN_SIMILARITY", str(_DEFAULT_MIN_SIM)))
    except ValueError:
        return _DEFAULT_MIN_SIM



def _language_instruction(*, audience_worker_simple: bool, forced_language: Literal["auto", "en", "bn"]) -> str:
    if forced_language == "bn":
        return " Answer fully in simple Bengali (বাংলা), regardless of question language."
    if forced_language == "en":
        return " Answer fully in plain English, regardless of question language."
    if audience_worker_simple:
        return (
            " Match the worker's language: if they write in Bengali (বাংলা), answer in simple, "
            "everyday Bengali they can understand quickly. If they write in English, answer in plain English. "
            "Start with a direct answer to their question, then add brief supporting detail if helpful."
        )
    return " Answer in the same language as the question when possible; stay professional and precise."


def rag_answer(
    question: str,
    *,
    role: Role,
    factory_id: str = "",
    top_k: int = 5,
    backend: BackendName | None = None,
    chroma_dir: Path | None = None,
    audience_worker_simple: bool = True,
    forced_language: Literal["auto", "en", "bn"] = "auto",
) -> tuple[str, list[ChromaHit]]:
    """Returns (assistant_reply, hits_used)."""
    q = question.strip()
    if audience_worker_simple and is_greeting_or_meta(q):
        print("(RAG) Greeting/meta — skipping retrieval; no document citations.", file=sys.stderr, flush=True)
        return greeting_reply(q, None if forced_language == "auto" else forced_language), []

    b = _resolve_backend(backend)

    print(
        "(RAG) Loading retriever; first call loads E5 then searches Chroma…",
        file=sys.stderr,
        flush=True,
    )
    engine = ChromaQueryEngine(chroma_dir) if chroma_dir else ChromaQueryEngine()
    hits = engine.search(question, role=role, factory_id=factory_id, top_k=top_k)

    min_sim = _min_similarity()
    trusted = [h for h in hits if h.similarity >= min_sim]
    if trusted:
        print(
            f"(RAG) {len(trusted)}/{len(hits)} chunk(s) above similarity {min_sim:.2f}",
            file=sys.stderr,
            flush=True,
        )
    else:
        print(
            f"(RAG) No chunks ≥ {min_sim:.2f} similarity — answering without trusted document excerpts.",
            file=sys.stderr,
            flush=True,
        )

    _llm_hint = "Groq API is usually a few seconds"
    print(
        f"(RAG) Calling {b} ({_llm_hint})…",
        file=sys.stderr,
        flush=True,
    )

    if trusted:
        ctx = _format_context(trusted)
        hits_for_client = trusted
    else:
        ctx = (
            "(No document excerpts met the relevance bar for this question. "
            "Do not cite specific laws or sections. Suggest the worker rephrase "
            "or ask about a concrete topic like leave, wages, or safety.)"
        )
        hits_for_client = []

    system = _system_prompt(
        audience_worker_simple=audience_worker_simple,
        forced_language=forced_language,
    )
    user = f"CONTEXT:\n{ctx}\n\nUSER QUESTION:\n{q}"
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    reply = chat(messages, backend=b)
    return reply.strip(), hits_for_client
