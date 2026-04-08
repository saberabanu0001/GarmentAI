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


@lru_cache
def get_settings() -> Settings:
    return Settings()
