"""Canonical role identifiers for RBAC. Import Role here — do not scatter raw strings."""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    """String values are stable API / metadata contract."""

    WORKER = "worker"
    SUPERVISOR = "supervisor"
    COMPLIANCE_OFFICER = "compliance_officer"
    HR_STAFF = "hr_staff"
    # Matches any requesting role (use sparingly in manifest).
    ALL = "all"


_ROLE_VALUES_NO_ALL = {r.value for r in Role if r is not Role.ALL}


def normalize_role_str(value: str) -> str:
    v = value.strip().lower()
    if v in _ROLE_VALUES_NO_ALL or v == Role.ALL.value:
        return v
    raise ValueError(
        f"Unknown role {value!r}. Use one of: {sorted(_ROLE_VALUES_NO_ALL | {Role.ALL.value})}"
    )


def validate_role_list(values: list[str]) -> list[str]:
    return [normalize_role_str(v) for v in values]


def roles_to_chroma_metadata(roles: list[str]) -> str:
    """Comma-separated string for Chroma metadata (no list type)."""
    ordered = validate_role_list(list(roles))
    return ",".join(ordered)


def parse_allowed_roles_csv(csv: str) -> frozenset[str]:
    if not csv or not csv.strip():
        return frozenset()
    parts = [normalize_role_str(p) for p in csv.split(",") if p.strip()]
    return frozenset(parts)


def role_may_access(allowed_roles_csv: str, requesting: Role) -> bool:
    allowed = parse_allowed_roles_csv(allowed_roles_csv)
    if Role.ALL.value in allowed:
        return True
    return requesting.value in allowed
