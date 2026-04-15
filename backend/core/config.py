"""Central paths and environment (single `.env` at repository root)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_repo_root() -> Path:
    # backend/core/config.py -> parents[2] == repository root
    return Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM (Groq-only for this deployment)
    llm_backend: str = "groq"
    groq_api_key: str | None = None
    groq_model: str | None = None
    ollama_host: str | None = None
    ollama_model: str | None = None
    gemini_api_key: str | None = None
    gemini_model: str | None = None
    whisper_api_key: str | None = None
    whisper_model: str = "whisper-large-v3"
    whisper_base_url: str | None = None

    # Auth (registration + JWT). Set JWT_SECRET for production.
    jwt_secret: str = "dev-only-change-me"
    jwt_expire_hours: int = 72
    auth_admin_key: str | None = None
    auth_auto_approve_registrations: bool = False
    enforce_auth_chat: bool = False  # also settable as ENFORCE_AUTH_CHAT
    database_url: str | None = None
    database_echo: bool = False
    # Cost-control guards for RAG (Phase 1)
    rag_enable_budget_enforcement: bool = False
    rag_daily_token_limit_per_tenant: int = 100_000
    rag_daily_request_limit_per_user: int = 400
    rag_reserved_completion_tokens: int = 500
    rag_cache_ttl_seconds: int = 1800
    rag_cache_max_entries: int = 2000
    rag_context_char_limit: int = 700
    rag_context_max_hits_default: int = 6
    rag_context_max_hits_hr: int = 8

    repo_root: Path | None = None

    @property
    def root(self) -> Path:
        return self.repo_root if self.repo_root is not None else _default_repo_root()

    @property
    def chroma_dir(self) -> Path:
        return self.root / "data" / "chroma_data"

    @property
    def chunks_dir(self) -> Path:
        return self.root / "data" / "chunked"

    @property
    def manifest_path(self) -> Path:
        return self.root / "backend" / "collection_manifest.yaml"

    @property
    def hf_cache_dir(self) -> Path:
        return self.root / "data" / ".hf_cache"

    @property
    def hr_dashboard_path(self) -> Path:
        """JSON file edited via HR UI (PUT /api/hr/dashboard)."""
        return self.root / "data" / "hr_dashboard.json"

    @property
    def auth_users_path(self) -> Path:
        return self.root / "data" / "auth_users.json"

    @property
    def auth_uploads_dir(self) -> Path:
        return self.root / "data" / "auth_uploads"

    @property
    def hr_uploads_dir(self) -> Path:
        return self.root / "data" / "hr_uploads"

    @property
    def hr_documents_index_path(self) -> Path:
        return self.root / "data" / "hr_documents_index.json"

    @property
    def rag_usage_path(self) -> Path:
        return self.root / "data" / "rag_usage_daily.json"

    @property
    def resolved_database_url(self) -> str | None:
        """Actual SQLAlchemy URL. Set DATABASE_URL=sqlite for a local file DB (beginner-friendly)."""
        raw = (self.database_url or "").strip()
        if not raw:
            return None
        if raw.lower() == "sqlite":
            path = (self.root / "data" / "garmentai.db").resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{path.as_posix()}"
        return raw


@lru_cache
def get_settings() -> Settings:
    return Settings()
