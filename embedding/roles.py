"""Compatibility shim — use `backend.core.security` in new code."""

from backend.core.security import (
    Role,
    normalize_role_str,
    parse_allowed_roles_csv,
    role_may_access,
    roles_to_chroma_metadata,
    validate_role_list,
)

__all__ = [
    "Role",
    "normalize_role_str",
    "parse_allowed_roles_csv",
    "role_may_access",
    "roles_to_chroma_metadata",
    "validate_role_list",
]
