"""JWT create/verify for GarmentAI auth."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from backend.core.config import get_settings


def create_access_token(*, user_id: str, email: str, role: str, verification_status: str) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "role": role,
        "ver": verification_status,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=s.jwt_expire_hours)).timestamp()),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any] | None:
    s = get_settings()
    try:
        return jwt.decode(token, s.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
