"""Pydantic models for HR dashboard JSON (API validation)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HrOverviewIn(BaseModel):
    workforceTotal: int = Field(ge=0, le=10_000_000)
    workforceTrendLabel: str = Field(max_length=200)
    activeViolations: int = Field(ge=0, le=1_000_000)
    pendingAudits: int = Field(ge=0, le=1_000_000)
    pendingAuditsHint: str = Field(max_length=500)


class HrAuditLogRowIn(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    timestampLabel: str = Field(max_length=120)
    category: str = Field(max_length=80)
    categoryVariant: Literal["overtime", "identity", "wage", "ppe"]
    summary: str = Field(max_length=2000)
    confidencePct: int = Field(ge=0, le=100)


class HrRegulatoryUpdateIn(BaseModel):
    title: str = Field(max_length=200)
    body: str = Field(max_length=4000)
    ctaLabel: str = Field(max_length=80)
    briefQuestion: str = Field(max_length=2000)


class HrAssistantIn(BaseModel):
    welcome: str = Field(max_length=4000)
    suggestedPrompt: str = Field(max_length=500)


class HrDashboardIn(BaseModel):
    overview: HrOverviewIn
    violationsNote: str = Field(max_length=2000)
    auditLog: list[HrAuditLogRowIn] = Field(default_factory=list)
    regulatoryUpdate: HrRegulatoryUpdateIn
    assistant: HrAssistantIn

    def to_api_dict(self) -> dict:
        return self.model_dump(mode="json")
