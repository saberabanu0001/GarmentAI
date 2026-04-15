"""Auth user store with DB-first mode and JSON fallback."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import bcrypt

from backend.core.config import get_settings

try:
    from backend.db.models import UserORM
    from backend.db.session import is_database_enabled, session_scope
except ModuleNotFoundError:
    UserORM = None  # type: ignore[assignment]

    def is_database_enabled() -> bool:  # type: ignore[no-redef]
        return False

    def session_scope() -> Any:  # type: ignore[no-redef]
        raise RuntimeError("Database mode unavailable: install sqlalchemy and pymysql")

VerificationStatus = Literal["pending", "approved", "rejected"]
AppRole = Literal["worker", "hr_staff", "compliance_officer"]

# Bcrypt ignores bytes after 72; keep hashing aligned with API max_length=72.
_MAX_PW_BYTES = 72


def _password_bytes(password: str) -> bytes:
    raw = password.encode("utf-8")
    return raw[:_MAX_PW_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("ascii")


def check_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            _password_bytes(password),
            password_hash.encode("ascii"),
        )
    except (ValueError, TypeError):
        return False


def _safe_filename(name: str) -> str:
    base = Path(name).name
    base = re.sub(r"[^a-zA-Z0-9._-]", "_", base)[:120]
    return base or "document.bin"


def _load_raw(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"users": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"users": []}
    if not isinstance(data, dict) or "users" not in data:
        return {"users": []}
    if not isinstance(data["users"], list):
        return {"users": []}
    return data


def _save_raw(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def find_user_by_email(email: str) -> dict[str, Any] | None:
    e = email.strip().lower()
    if is_database_enabled() and UserORM is not None:
        with session_scope() as session:
            row = session.query(UserORM).filter(UserORM.email == e).first()
            return _row_to_dict(row) if row else None
    path = get_settings().auth_users_path
    for u in _load_raw(path)["users"]:
        if isinstance(u, dict) and str(u.get("email", "")).lower() == e:
            return u
    return None


def register_user(
    *,
    email: str,
    password: str,
    role: AppRole,
    verification_bytes: bytes,
    verification_filename: str,
) -> dict[str, Any]:
    s = get_settings()
    e = email.strip().lower()
    if find_user_by_email(e):
        raise ValueError("email already registered")

    uid = str(uuid.uuid4())
    rel = f"{uid}/{_safe_filename(verification_filename)}"
    dest = s.auth_uploads_dir / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(verification_bytes)

    status: VerificationStatus = "approved" if s.auth_auto_approve_registrations else "pending"
    user = {
        "id": uid,
        "email": e,
        "password_hash": hash_password(password),
        "role": role,
        "verification_status": status,
        "verification_doc_rel_path": rel,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if is_database_enabled() and UserORM is not None:
        with session_scope() as session:
            session.add(
                UserORM(
                    id=uid,
                    email=e,
                    password_hash=user["password_hash"],
                    role=role,
                    verification_status=status,
                    verification_doc_rel_path=rel,
                )
            )
        return user
    path = get_settings().auth_users_path
    data = _load_raw(path)
    data["users"].append(user)
    _save_raw(path, data)
    return user


def verify_password(user: dict[str, Any], password: str) -> bool:
    h = user.get("password_hash")
    if not isinstance(h, str):
        return False
    return check_password(password, h)


def set_user_verification(email: str, status: VerificationStatus) -> dict[str, Any]:
    e = email.strip().lower()
    if is_database_enabled() and UserORM is not None:
        with session_scope() as session:
            row = session.query(UserORM).filter(UserORM.email == e).first()
            if row is None:
                raise ValueError("user not found")
            row.verification_status = status
            session.add(row)
            session.flush()
            return _row_to_dict(row)
    path = get_settings().auth_users_path
    data = _load_raw(path)
    for u in data["users"]:
        if isinstance(u, dict) and str(u.get("email", "")).lower() == e:
            u["verification_status"] = status
            _save_raw(path, data)
            return u
    raise ValueError("user not found")


def _row_to_dict(row: Any) -> dict[str, Any]:
    created = row.created_at
    created_at = created.isoformat() if isinstance(created, datetime) else str(created)
    return {
        "id": row.id,
        "email": row.email,
        "password_hash": row.password_hash,
        "role": row.role,
        "verification_status": row.verification_status,
        "verification_doc_rel_path": row.verification_doc_rel_path,
        "created_at": created_at,
    }


def user_public(u: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": u["id"],
        "email": u["email"],
        "role": u["role"],
        "verification_status": u["verification_status"],
    }
