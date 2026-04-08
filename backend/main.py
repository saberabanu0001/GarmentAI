"""
Garment-AI FastAPI entrypoint.

From repository root:
  uvicorn backend.main:app --reload --host 127.0.0.1 --port 5050
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.audit import router as audit_router
from backend.api.chat import router as chat_router
from backend.api.documents import router as documents_router
from backend.api.voice import router as voice_router

app = FastAPI(title="GarmentAI API", version="1.0.0")


@app.exception_handler(HTTPException)
async def _http_error(_request: Request, exc: HTTPException) -> JSONResponse:
    d = exc.detail
    if isinstance(d, dict) and "error" in d:
        return JSONResponse(status_code=exc.status_code, content=d)
    return JSONResponse(status_code=exc.status_code, content={"error": str(d)})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(audit_router)
app.include_router(documents_router)
app.include_router(voice_router)


@app.get("/")
def index() -> dict[str, str | list[str]]:
    return {
        "service": "GarmentAI API",
        "endpoints": [
            "GET /health",
            "POST /api/chat",
            "POST /api/rag",
            "GET /api/hr/dashboard",
            "PUT /api/hr/dashboard",
            "GET /api/audit/dashboard",
            "POST /api/upload",
            "POST /api/voice/transcribe",
        ],
        "ui": "Run Next.js from frontend/ and open http://localhost:3000",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
