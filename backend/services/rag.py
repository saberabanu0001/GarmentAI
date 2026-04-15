"""RAG: Chroma retrieval + LLM answer."""

from __future__ import annotations

import os
import re
import sys
from dataclasses import replace
from pathlib import Path
from typing import Literal

from backend.core.config import get_settings
from backend.core.security import Role
from backend.services import rag_cache
from backend.services.rag_budget import enforce_and_consume, estimate_tokens
from backend.services.chroma_engine import ChromaHit, ChromaQueryEngine
from backend.services.llm_wrapper import BackendName, chat

from backend.services.rag_intent import greeting_reply, is_greeting_or_meta

# Cosine similarity from Chroma (higher = closer). Below this, we do not trust chunks for display or context.
_DEFAULT_MIN_SIM = 0.52
_HR_UPLOADS_COLLECTION = "hr_uploads"
_DEFAULT_CLIENT_CITATIONS = 8
_HR_PERSONAL_CITATIONS = 6
_PERSONAL_HINT_WORDS = (
    "salary",
    "payroll",
    "basic salary",
    "bonus",
    "deduction",
    "net salary",
    "interview",
    "evaluation",
    "education",
    "qualification",
    "experience",
    "efficiency",
    "worker",
    "candidate",
    "joining",
    "leave",
)
_PERSON_NAME_RE = re.compile(
    r"\b(?:md\.?|mr\.?|mrs\.?|ms\.?|dr\.?)?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b"
)


def _is_hr_like_role(role: Role) -> bool:
    return role in (Role.HR_STAFF, Role.COMPLIANCE_OFFICER)


def _looks_personnel_query(question: str) -> bool:
    q = question.strip()
    if not q:
        return False
    q_low = q.lower()
    if _PERSON_NAME_RE.search(q):
        return True
    return any(tok in q_low for tok in _PERSONAL_HINT_WORDS)


def _prioritize_hr_uploads_in_context(hits: list[ChromaHit], role: Role) -> list[ChromaHit]:
    """Put hr_uploads first so the LLM sees internal records before generic law text."""
    if role not in (Role.HR_STAFF, Role.COMPLIANCE_OFFICER) or not hits:
        return hits
    hr = [h for h in hits if h.collection == _HR_UPLOADS_COLLECTION]
    rest = [h for h in hits if h.collection != _HR_UPLOADS_COLLECTION]
    merged = hr + rest
    return [replace(h, rank=i) for i, h in enumerate(merged, start=1)]


def _format_context(
    hits: list[ChromaHit],
    *,
    hr_staff_style: bool = False,
    context_char_limit: int = 700,
) -> str:
    blocks: list[str] = []
    for h in hits:
        lead = ""
        if hr_staff_style and h.collection == _HR_UPLOADS_COLLECTION:
            lead = (
                "INTERNAL HR UPLOAD — use for worker-specific facts (pay, leave, performance) "
                "when this text contains them:\n"
            )
        header = f"[{h.rank}] {h.collection} | {h.source_name} | {h.document_name}"
        if str(h.section).strip():
            header += f" | {h.section}"
        text = (h.text or "").strip()
        if len(text) > context_char_limit:
            text = text[: context_char_limit - 1].rstrip() + "…"
        blocks.append(f"{lead}{header}\n{text}")
    return "\n\n---\n\n".join(blocks)


def _select_context_hits(question: str, hits: list[ChromaHit], role: Role) -> list[ChromaHit]:
    """Keep context focused: for personnel queries, lead heavily with hr_uploads."""
    s = get_settings()
    max_hits = (
        s.rag_context_max_hits_hr if _is_hr_like_role(role) else s.rag_context_max_hits_default
    )
    if not hits:
        return hits
    if not _is_hr_like_role(role):
        return hits[:max_hits]
    if not _looks_personnel_query(question):
        return hits[:max_hits]

    hr = [h for h in hits if h.collection == _HR_UPLOADS_COLLECTION]
    if not hr:
        return hits[:max_hits]
    rest = [h for h in hits if h.collection != _HR_UPLOADS_COLLECTION]
    merged = hr[:max_hits] + rest
    trimmed = merged[:max_hits]
    return [replace(h, rank=i) for i, h in enumerate(trimmed, start=1)]


def _select_client_citations(question: str, hits: list[ChromaHit], role: Role) -> list[ChromaHit]:
    """Prune noisy citations in UI while preserving useful traceability."""
    if not hits:
        return []
    if not _is_hr_like_role(role):
        return hits[:_DEFAULT_CLIENT_CITATIONS]
    if _looks_personnel_query(question):
        hr = [h for h in hits if h.collection == _HR_UPLOADS_COLLECTION]
        if hr:
            trimmed = hr[:_HR_PERSONAL_CITATIONS]
            return [replace(h, rank=i) for i, h in enumerate(trimmed, start=1)]
    trimmed = hits[:_DEFAULT_CLIENT_CITATIONS]
    return [replace(h, rank=i) for i, h in enumerate(trimmed, start=1)]


def _system_prompt(*, audience_worker_simple: bool, forced_language: Literal["auto", "en", "bn"] = "auto") -> str:
    if audience_worker_simple:
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
    else:
        base = (
            "You are GarmentAI, an assistant for HR and compliance staff in garment factories. "
            "Use ONLY the CONTEXT excerpts below. "
            "If INTERNAL HR UPLOAD excerpts (collection hr_uploads) state specific facts—amounts, names, "
            "dates, leave, efficiency, deductions—you MUST answer from them; do not say the detail was "
            "not found when those facts appear in any such excerpt. "
            "If something is truly absent from every excerpt, say honestly that this detail was not found "
            "(do not invent rules or numbers). "
            "For general legal standards (not worker-specific records), prefer statute and policy excerpts. "
            "Write clearly and professionally. "
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
    requester_key: str = "",
) -> tuple[str, list[ChromaHit]]:
    """Returns (assistant_reply, hits_used)."""
    q = question.strip()
    if audience_worker_simple and is_greeting_or_meta(q):
        print("(RAG) Greeting/meta — skipping retrieval; no document citations.", file=sys.stderr, flush=True)
        return greeting_reply(q, None if forced_language == "auto" else forced_language), []

    b = _resolve_backend(backend)
    s = get_settings()

    cache_key = rag_cache.make_key(
        question=q,
        role=role.value,
        factory_id=factory_id,
        top_k=top_k,
        forced_language=forced_language,
    )
    cached = rag_cache.get_cached(cache_key)
    if cached is not None:
        print("(RAG) Cache hit.", file=sys.stderr, flush=True)
        return cached

    print(
        "(RAG) Loading retriever; first call loads E5 then searches Chroma…",
        file=sys.stderr,
        flush=True,
    )
    engine = ChromaQueryEngine(chroma_dir) if chroma_dir else ChromaQueryEngine()
    effective_top_k = top_k
    if role in (Role.HR_STAFF, Role.COMPLIANCE_OFFICER):
        # Wide enough for several hr_uploads chunks plus law/policy after recall widening.
        effective_top_k = max(top_k, 14)
    hits = engine.search(
        question,
        role=role,
        factory_id=factory_id,
        top_k=effective_top_k,
    )

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
        hr_style = _is_hr_like_role(role)
        ordered = _prioritize_hr_uploads_in_context(trusted, role) if hr_style else trusted
        context_hits = _select_context_hits(q, ordered, role)
        ctx = _format_context(
            context_hits,
            hr_staff_style=hr_style,
            context_char_limit=s.rag_context_char_limit,
        )
        hits_for_client = _select_client_citations(q, context_hits, role)
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
    estimated = estimate_tokens(system) + estimate_tokens(user) + s.rag_reserved_completion_tokens
    enforce_and_consume(
        tenant_key=factory_id or "global",
        user_key=requester_key or f"role:{role.value}",
        estimated_tokens=estimated,
        request_inc=1,
    )
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    reply = chat(messages, backend=b)
    final_reply = reply.strip()
    rag_cache.set_cached(
        key=cache_key,
        answer=final_reply,
        hits=hits_for_client,
        ttl_seconds=s.rag_cache_ttl_seconds,
        max_entries=s.rag_cache_max_entries,
    )
    return final_reply, hits_for_client
