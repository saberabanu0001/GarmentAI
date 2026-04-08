"""HR dashboard payload — served via GET /api/hr/dashboard; replace with DB later."""

from __future__ import annotations

HR_DASHBOARD: dict = {
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


def get_hr_dashboard() -> dict:
    return HR_DASHBOARD
