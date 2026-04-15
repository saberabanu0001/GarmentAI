"""HTTP Bearer token parsing for FastAPI."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Header, HTTPException

from backend.services.auth_tokens import decode_access_token


async def optional_bearer_token(
    authorization: Annotated[str | None, Header()] = None,
) -> dict | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    raw = authorization.split(" ", 1)[1].strip()
    if not raw:
        return None
    payload = decode_access_token(raw)
    if not payload:
        return None
    return payload


def token_role(payload: dict) -> str:
    r = payload.get("role")
    return str(r) if r is not None else ""


def require_roles_allowed(*allowed_roles: str) -> Callable[..., dict]:
    """FastAPI dependency: valid Bearer JWT and role in allowed_roles."""
    allowed = frozenset(allowed_roles)

    def _dep(authorization: Annotated[str | None, Header()] = None) -> dict:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(
                status_code=401,
                detail={"error": "authentication required"},
            )
        raw = authorization.split(" ", 1)[1].strip()
        payload = decode_access_token(raw)
        if not payload:
            raise HTTPException(
                status_code=401,
                detail={"error": "invalid or expired token"},
            )
        role = token_role(payload)
        if role not in allowed:
            raise HTTPException(
                status_code=403,
                detail={"error": "insufficient role", "role": role},
            )
        return payload

    return _dep


require_hr_staff = require_roles_allowed("hr_staff")
