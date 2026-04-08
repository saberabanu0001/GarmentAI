"""HR dashboard: defaults + persisted JSON at data/hr_dashboard.json."""

from __future__ import annotations

import json
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any

from backend.core.config import get_settings
from backend.schemas.hr_dashboard import HrDashboardIn

_LOCK = threading.Lock()

DEFAULT_HR_DASHBOARD: dict[str, Any] = {
    "overview": {
        "workforceTotal": 500,
        "workforceTrendLabel": "+4% vs last month",
        "activeViolations": 12,
        "pendingAudits": 3,
        "pendingAuditsHint": "Next scheduled: Floor 3, Line 4.",
    },
    "violationsNote": (
        "Requires immediate HR intervention — from rules engine / audit queue "
        "(replace with live counts from your systems)."
    ),
    "auditLog": [
        {
            "id": "1",
            "timestampLabel": "11:42 AM",
            "category": "OVERTIME",
            "categoryVariant": "overtime",
            "summary": (
                "ID #204: Overtime violation flagged by rules engine "
                "(served from API — swap data source when DB is ready)."
            ),
            "confidencePct": 98,
        },
        {
            "id": "2",
            "timestampLabel": "Yesterday",
            "category": "PPE",
            "categoryVariant": "ppe",
            "summary": (
                "Floor A: PPE checklist item pending verification "
                "(served from API)."
            ),
            "confidencePct": 84,
        },
    ],
    "regulatoryUpdate": {
        "title": "Regulatory update",
        "body": (
            "New ILO / buyer standards — this text is served from the API; "
            "point hr_data or a DB row at your content feed when ready."
        ),
        "ctaLabel": "Read brief",
        "briefQuestion": (
            "Summarize the latest ILO and buyer compliance expectations "
            "relevant to garment factory HR, based on our indexed documents."
        ),
    },
    "assistant": {
        "welcome": (
            "Hello, HR Manager. Ask policy questions below — answers use your "
            "indexed library via the same RAG pipeline as the worker portal."
        ),
        "suggestedPrompt": "Summarize new overtime regulations…",
    },
}


def _store_path() -> Path:
    return get_settings().hr_dashboard_path


def _read_raw_file(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(raw, dict):
        return None
    return raw


def get_hr_dashboard() -> dict[str, Any]:
    """Return saved dashboard if valid; otherwise in-memory defaults."""
    path = _store_path()
    with _LOCK:
        stored = _read_raw_file(path)
    if stored is None:
        return deepcopy(DEFAULT_HR_DASHBOARD)
    try:
        validated = HrDashboardIn.model_validate(stored)
        return validated.to_api_dict()
    except Exception:
        return deepcopy(DEFAULT_HR_DASHBOARD)


def save_hr_dashboard(payload: HrDashboardIn) -> dict[str, Any]:
    """Validate, write JSON, return canonical dict."""
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = payload.to_api_dict()
    text = json.dumps(data, ensure_ascii=False, indent=2)
    with _LOCK:
        path.write_text(text + "\n", encoding="utf-8")
    return data
