"""Unit tests for canonical roles and RBAC helpers (no Chroma / E5)."""

from __future__ import annotations

import pytest

from backend.core.security import (
    Role,
    normalize_role_str,
    role_may_access,
    validate_role_list,
)
from backend.services.merge_policy import merge_tier


def test_normalize_role_accepts_canonical() -> None:
    assert normalize_role_str("WORKER") == "worker"
    assert normalize_role_str("Hr_Staff") == "hr_staff"


def test_normalize_role_rejects_typo() -> None:
    with pytest.raises(ValueError, match="Unknown role"):
        normalize_role_str("compliance")


def test_validate_role_list() -> None:
    assert validate_role_list(["worker", "hr_staff"]) == ["worker", "hr_staff"]


def test_role_may_access_all() -> None:
    assert role_may_access("all", Role.WORKER) is True
    assert role_may_access("all", Role.HR_STAFF) is True


def test_role_may_access_hr_only_blocks_worker() -> None:
    allowed = "hr_staff"
    assert role_may_access(allowed, Role.HR_STAFF) is True
    assert role_may_access(allowed, Role.WORKER) is False


def test_merge_tier_order() -> None:
    assert merge_tier("tenant") < merge_tier("compliance")
    assert merge_tier("compliance") < merge_tier("global_law")


def test_candidate_sort_tie_break() -> None:
    a = {"similarity": 0.8, "doc_scope": "global_law"}
    b = {"similarity": 0.8, "doc_scope": "tenant"}
    items = [a, b]
    items.sort(key=lambda x: (-x["similarity"], merge_tier(x["doc_scope"])))
    assert items[0]["doc_scope"] == "tenant"
