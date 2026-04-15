"""Small in-memory cache for repeated RAG questions."""

from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from typing import Literal

from backend.services.chroma_engine import ChromaHit

_LOCK = threading.Lock()
_CACHE: OrderedDict[str, tuple[float, str, list[dict[str, object]]]] = OrderedDict()


def _normalize(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def make_key(
    *,
    question: str,
    role: str,
    factory_id: str,
    top_k: int,
    forced_language: Literal["auto", "en", "bn"],
) -> str:
    raw = "||".join(
        [
            _normalize(question),
            role.strip().lower(),
            (factory_id or "").strip().lower(),
            str(top_k),
            forced_language,
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def clear_all() -> None:
    with _LOCK:
        _CACHE.clear()


def get_cached(key: str) -> tuple[str, list[ChromaHit]] | None:
    now = time.time()
    with _LOCK:
        row = _CACHE.get(key)
        if row is None:
            return None
        exp, answer, hits_raw = row
        if exp <= now:
            _CACHE.pop(key, None)
            return None
        # LRU refresh
        _CACHE.move_to_end(key)
        hits = [ChromaHit(**h) for h in hits_raw]
        return answer, hits


def set_cached(
    *,
    key: str,
    answer: str,
    hits: list[ChromaHit],
    ttl_seconds: int,
    max_entries: int,
) -> None:
    exp = time.time() + max(1, ttl_seconds)
    hits_raw: list[dict[str, object]] = [h.to_dict() for h in hits]
    with _LOCK:
        _CACHE[key] = (exp, answer, hits_raw)
        _CACHE.move_to_end(key)
        while len(_CACHE) > max(1, max_entries):
            _CACHE.popitem(last=False)

