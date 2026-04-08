"""Compliance / HR dashboard endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.schemas.hr_dashboard import HrDashboardIn
from backend.services.hr_data import get_hr_dashboard, save_hr_dashboard

router = APIRouter(tags=["audit"])


@router.get("/api/hr/dashboard")
def hr_dashboard() -> dict:
    return get_hr_dashboard()


@router.put("/api/hr/dashboard")
def hr_dashboard_put(body: HrDashboardIn) -> dict:
    """Replace entire dashboard; persisted to data/hr_dashboard.json."""
    try:
        return save_hr_dashboard(body)
    except OSError as e:
        raise HTTPException(status_code=500, detail={"error": f"Could not save: {e}"}) from e


@router.get("/api/audit/dashboard")
def audit_dashboard() -> dict:
    """Same payload as HR dashboard (team naming)."""
    return get_hr_dashboard()
