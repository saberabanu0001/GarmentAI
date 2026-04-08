"""Compatibility shim."""

from backend.core.config import get_settings
from backend.services.manifest_loader import (
    ManifestRule,
    chunk_uid,
    load_manifest,
    resolve_manifest_rule,
)

MANIFEST_PATH = get_settings().manifest_path

__all__ = [
    "MANIFEST_PATH",
    "ManifestRule",
    "chunk_uid",
    "load_manifest",
    "resolve_manifest_rule",
]
