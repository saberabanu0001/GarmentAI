"""SQLAlchemy ORM models for auth and document ingestion workflow."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import CHAR, BigInteger, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("worker", "hr_staff", "compliance_officer", name="user_role"),
        nullable=False,
    )
    verification_status: Mapped[str] = mapped_column(
        Enum("pending", "approved", "rejected", name="verification_status"),
        nullable=False,
    )
    verification_doc_rel_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


class DocumentORM(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    factory_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    doc_type: Mapped[str] = mapped_column(
        Enum("policy", "law", "contract", "sop", "notice", "other", name="document_type"),
        nullable=False,
        default="other",
    )
    source: Mapped[str] = mapped_column(
        Enum("hr_upload", "admin_upload", "system_import", name="document_source"),
        nullable=False,
        default="hr_upload",
    )
    status: Mapped[str] = mapped_column(
        Enum("draft", "pending_review", "approved", "rejected", "archived", name="document_status"),
        nullable=False,
        default="draft",
    )
    visibility: Mapped[str] = mapped_column(
        Enum("worker", "hr_staff", "compliance_officer", "all", name="document_visibility"),
        nullable=False,
        default="all",
    )
    created_by_user_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id"), nullable=False)
    approved_by_user_id: Mapped[str | None] = mapped_column(CHAR(36), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_version_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index("idx_documents_scope", "tenant_id", "factory_id", "status"),
        Index("idx_documents_visibility", "visibility", "status"),
        Index("idx_documents_created_at", "created_at"),
    )


class DocumentVersionORM(Base):
    __tablename__ = "document_versions"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_provider: Mapped[str] = mapped_column(
        Enum("local", "s3", "minio", name="storage_provider"),
        nullable=False,
        default="local",
    )
    storage_bucket: Mapped[str | None] = mapped_column(String(128), nullable=True)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(127), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str | None] = mapped_column(CHAR(64), nullable=True)
    extraction_status: Mapped[str] = mapped_column(
        Enum("queued", "processing", "done", "failed", name="extraction_status"),
        nullable=False,
        default="queued",
    )
    extraction_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by_user_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("idx_doc_versions_doc", "document_id", "created_at"),
        Index("idx_doc_versions_extract", "extraction_status", "created_at"),
        Index("uq_doc_version", "document_id", "version_no", unique=True),
    )


class IngestionJobORM(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    document_version_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    trigger_reason: Mapped[str] = mapped_column(
        Enum("approve", "replace", "reindex", "delete", name="ingestion_trigger_reason"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum("queued", "running", "succeeded", "failed", "cancelled", name="ingestion_job_status"),
        nullable=False,
        default="queued",
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    worker_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("idx_ingestion_status", "status", "created_at"),
        Index("idx_ingestion_version", "document_version_id", "created_at"),
    )
