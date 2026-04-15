"""Daily quota helpers for RAG token/request controls."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from backend.core.config import get_settings

_LOCK = threading.Lock()
_STATE: dict[str, Any] | None = None


@dataclass
class QuotaExceededError(RuntimeError):
    message: str
    retry_after_seconds: int

    def __str__(self) -> str:
        return self.message


def estimate_tokens(text: str) -> int:
    """Cheap approximation to avoid tokenizer dependency in MVP."""
    n = len((text or "").strip())
    if n <= 0:
        return 1
    return max(1, n // 4)


def _day_key_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def _seconds_until_next_utc_day() -> int:
    now = datetime.now(UTC)
    nxt = datetime(year=now.year, month=now.month, day=now.day, tzinfo=UTC) + timedelta(days=1)
    return max(60, int((nxt - now).total_seconds()))


def _blank_state(day_key: str) -> dict[str, Any]:
    return {"day": day_key, "tenants": {}, "users": {}}


def _load_state_if_needed() -> dict[str, Any]:
    global _STATE
    day = _day_key_utc()
    if _STATE is not None and str(_STATE.get("day", "")) == day:
        return _STATE

    s = get_settings()
    path = s.rag_usage_path
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and str(raw.get("day", "")) == day:
            _STATE = raw
            return _STATE
    except (OSError, json.JSONDecodeError):
        pass

    _STATE = _blank_state(day)
    return _STATE


def _persist_state(state: dict[str, Any]) -> None:
    s = get_settings()
    path = s.rag_usage_path
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        # Budget enforcement should not crash if usage logging fails.
        return


def enforce_and_consume(
    *,
    tenant_key: str,
    user_key: str,
    estimated_tokens: int,
    request_inc: int = 1,
) -> None:
    s = get_settings()
    if not s.rag_enable_budget_enforcement:
        return

    t_key = tenant_key.strip() or "global"
    u_key = user_key.strip() or "anonymous"
    token_inc = max(1, int(estimated_tokens))
    req_inc = max(1, int(request_inc))

    with _LOCK:
        state = _load_state_if_needed()
        tenants = state.setdefault("tenants", {})
        users = state.setdefault("users", {})
        t_used = int(tenants.get(t_key, 0))
        u_used = int(users.get(u_key, 0))

        if t_used + token_inc > s.rag_daily_token_limit_per_tenant:
            raise QuotaExceededError(
                message=(
                    f"Daily AI token budget reached for tenant '{t_key}'. "
                    f"Try again after reset."
                ),
                retry_after_seconds=_seconds_until_next_utc_day(),
            )
        if u_used + req_inc > s.rag_daily_request_limit_per_user:
            raise QuotaExceededError(
                message=(
                    f"Daily AI request limit reached for user '{u_key}'. "
                    f"Try again after reset."
                ),
                retry_after_seconds=_seconds_until_next_utc_day(),
            )

        tenants[t_key] = t_used + token_inc
        users[u_key] = u_used + req_inc
        _persist_state(state)

