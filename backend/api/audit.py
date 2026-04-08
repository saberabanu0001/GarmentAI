"""Compliance / HR dashboard endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.services.hr_data import get_hr_dashboard

router = APIRouter(tags=["audit"])


@router.get("/api/hr/dashboard")
def hr_dashboard() -> dict:
    return get_hr_dashboard()


@router.get("/api/audit/dashboard")
def audit_dashboard() -> dict:
    """Same payload as HR dashboard (team naming)."""
    return get_hr_dashboard()
