"""Registration, login, and verification workflow."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, EmailStr, Field, TypeAdapter, ValidationError

from backend.core.auth_http import optional_bearer_token
from backend.core.config import get_settings
from backend.services import auth_store
from backend.services.auth_tokens import create_access_token

router = APIRouter(tags=["auth"])

RegisterRole = Literal["worker", "hr_staff", "compliance_officer"]


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ApproveIn(BaseModel):
    email: EmailStr
    status: Literal["approved", "rejected"] = "approved"


@router.post("/api/auth/register")
async def register(
    email: str = Form(...),
    password: str = Form(..., min_length=6, max_length=72),
    role: RegisterRole = Form(...),
    verification_doc: UploadFile = File(...),
) -> dict:
    try:
        email = str(TypeAdapter(EmailStr).validate_python(email))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"error": "invalid email"}) from e
    content = await verification_doc.read()
    if not content:
        raise HTTPException(status_code=400, detail={"error": "verification document is required"})
    if len(content) > 6 * 1024 * 1024:
        raise HTTPException(status_code=400, detail={"error": "file too large (max 6MB)"})
    try:
        user = auth_store.register_user(
            email=email,
            password=password,
            role=role,
            verification_bytes=content,
            verification_filename=verification_doc.filename or "document",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": str(e)}) from e
    return {
        "ok": True,
        "user": auth_store.user_public(user),
        "message": (
            "Account created. You can sign in once your documents are approved."
            if user["verification_status"] == "pending"
            else "Account created and approved. You can sign in."
        ),
    }


@router.post("/api/auth/login", response_model=LoginOut)
def login(body: LoginIn) -> LoginOut:
    user = auth_store.find_user_by_email(body.email)
    if not user or not auth_store.verify_password(user, body.password):
        raise HTTPException(status_code=401, detail={"error": "invalid email or password"})

    s = get_settings()
    if user.get("verification_status") != "approved":
        # Accounts created before AUTH_AUTO_APPROVE_REGISTRATIONS=true stay "pending"
        # in auth_users.json; promote on login when demo auto-approve is enabled.
        st = user.get("verification_status")
        if s.auth_auto_approve_registrations and st == "pending":
            user = auth_store.set_user_verification(str(user["email"]), "approved")
        elif st == "pending":
            raise HTTPException(
                status_code=403,
                detail={"error": "account pending verification", "status": st},
            )
        elif st == "rejected":
            raise HTTPException(status_code=403, detail={"error": "account rejected"})
        else:
            raise HTTPException(status_code=403, detail={"error": "account not approved"})
    token = create_access_token(
        user_id=str(user["id"]),
        email=str(user["email"]),
        role=str(user["role"]),
        verification_status=str(user["verification_status"]),
    )
    return LoginOut(access_token=token, user=auth_store.user_public(user))


@router.get("/api/auth/me")
def me(payload: dict | None = Depends(optional_bearer_token)) -> dict:
    if not payload:
        raise HTTPException(status_code=401, detail={"error": "not authenticated"})
    user = auth_store.find_user_by_email(str(payload.get("email", "")))
    if not user:
        raise HTTPException(status_code=401, detail={"error": "user not found"})
    return auth_store.user_public(user)


@router.post("/api/auth/approve")
def approve(
    body: ApproveIn,
    x_admin_key: Annotated[str | None, Header()] = None,
) -> dict:
    s = get_settings()
    if not s.auth_admin_key or x_admin_key != s.auth_admin_key:
        raise HTTPException(status_code=403, detail={"error": "admin key required"})
    try:
        user = auth_store.set_user_verification(body.email, body.status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": str(e)}) from e
    return {"ok": True, "user": auth_store.user_public(user)}
