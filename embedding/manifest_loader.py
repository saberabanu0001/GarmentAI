"""Load collection_manifest.yaml and resolve per-chunk-file routing + RBAC metadata."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from embedding.roles import roles_to_chroma_metadata, validate_role_list

MANIFEST_PATH = Path(__file__).resolve().parent / "collection_manifest.yaml"


@dataclass(frozen=True)
class ManifestRule:
    pattern: str
    collection: str
    doc_scope: str
    doc_category: str
    language: str
    factory_id: str
    allowed_roles_csv: str


def _load_raw(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Manifest not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "rules" not in data:
        raise ValueError("Manifest must be a mapping with key 'rules'")
    rules = data["rules"]
    if not isinstance(rules, list) or not rules:
        raise ValueError("Manifest 'rules' must be a non-empty list")
    return data


def load_manifest(path: Path | None = None) -> list[ManifestRule]:
    raw = _load_raw(path or MANIFEST_PATH)
    out: list[ManifestRule] = []
    for i, row in enumerate(raw["rules"]):
        if not isinstance(row, dict):
            raise ValueError(f"rules[{i}] must be a mapping")
        try:
            roles = validate_role_list(list(row["allowed_roles"]))
        except KeyError as e:
            raise ValueError(f"rules[{i}] missing {e}") from e
        try:
            out.append(
                ManifestRule(
                    pattern=str(row["pattern"]),
                    collection=str(row["collection"]),
                    doc_scope=str(row["doc_scope"]),
                    doc_category=str(row["doc_category"]),
                    language=str(row["language"]),
                    factory_id=str(row.get("factory_id", "") or ""),
                    allowed_roles_csv=roles_to_chroma_metadata(roles),
                )
            )
        except KeyError as e:
            raise ValueError(f"rules[{i}] missing required field: {e}") from e
    return out


def resolve_manifest_rule(chunks_filename: str, rules: list[ManifestRule]) -> ManifestRule:
    name = Path(chunks_filename).name
    for rule in rules:
        if fnmatch.fnmatch(name, rule.pattern):
            return rule
    raise ValueError(
        f"No manifest rule matches {name!r}. Add a pattern to {MANIFEST_PATH.name}."
    )


def chunk_uid(factory_id: str, chunks_filename: str, chunk_id: int) -> str:
    tenant = factory_id.strip() or "global"
    return f"{tenant}:{Path(chunks_filename).name}:{chunk_id}"
