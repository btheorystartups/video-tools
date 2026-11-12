"""Dependency and reference hashing for portable export cache decisions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from asset_dependency_scanner import extract_references, is_text_file, resolve_reference
from portable_package_size_report import sha256_file
from stability import utc_now_iso, write_json

TIMESTAMP_KEYS = {
    "generated_at_utc",
    "generation_timestamp",
    "last_exported",
    "last_validated",
    "last_modified",
    "zip_path",
    "package_root",
}


def _relative_to_root(path: Path, root: Path) -> str | None:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def metadata_hash(path: Path) -> str:
    stat = path.stat()
    payload = {"name": path.name, "suffix": path.suffix.lower(), "size": stat.st_size}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def semantic_content_hash(path: Path) -> str:
    """Hash content with volatile exporter timestamps removed for JSON evidence."""
    if path.suffix.lower() != ".json":
        return sha256_file(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return sha256_file(path)
    return hashlib.sha256(json.dumps(_strip_volatile(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _strip_volatile(value):
    if isinstance(value, dict):
        return {key: _strip_volatile(item) for key, item in value.items() if key not in TIMESTAMP_KEYS}
    if isinstance(value, list):
        return [_strip_volatile(item) for item in value]
    return value


def reference_hash(path: Path, root: Path) -> str:
    if not is_text_file(path):
        return ""
    refs = []
    for ref in extract_references(path):
        value = str(ref.get("value") or "")
        resolved = resolve_reference(path, root, value)
        rel = _relative_to_root(resolved, root) if resolved and resolved.exists() and resolved.is_file() else None
        refs.append(
            {
                "kind": ref.get("kind"),
                "value": value.replace("\\", "/"),
                "resolved": rel,
            }
        )
    return hashlib.sha256(json.dumps(sorted(refs, key=lambda row: json.dumps(row, sort_keys=True)), sort_keys=True).encode("utf-8")).hexdigest()


def dependency_hash(path: Path, root: Path) -> str:
    if not is_text_file(path):
        return ""
    deps = []
    for ref in extract_references(path):
        resolved = resolve_reference(path, root, str(ref.get("value") or ""))
        rel = _relative_to_root(resolved, root) if resolved and resolved.exists() and resolved.is_file() else None
        if rel:
            deps.append({"path": rel, "hash": sha256_file(resolved)})
    return hashlib.sha256(json.dumps(sorted(deps, key=lambda row: row["path"]), sort_keys=True).encode("utf-8")).hexdigest()


def build_dependency_hash_registry(package_root: Path) -> dict:
    rows = []
    for path in sorted(package_root.rglob("*"), key=lambda item: item.relative_to(package_root).as_posix().lower()):
        if not path.is_file():
            continue
        rel = path.relative_to(package_root).as_posix()
        rows.append(
            {
                "package_path": rel,
                "content_hash": semantic_content_hash(path),
                "metadata_hash": metadata_hash(path),
                "reference_hash": reference_hash(path, package_root),
                "dependency_hash": dependency_hash(path, package_root),
            }
        )
    registry = {
        "analysis_status": "complete",
        "method": "dependency_hash_registry_v67",
        "generated_at_utc": utc_now_iso(),
        "artifacts": rows,
        "summary": {"artifact_count": len(rows), "text_artifact_count": sum(1 for row in rows if row["reference_hash"])},
    }
    write_json(package_root / "dependency_hash_registry.json", registry)
    write_json(package_root / "validation" / "dependency_hash_registry.json", registry)
    return registry
