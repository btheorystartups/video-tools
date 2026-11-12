"""Stable artifact identity helpers for portable exports."""

from __future__ import annotations

from pathlib import Path

from stability import deterministic_id


def normalize_artifact_path(path: str | Path) -> str:
    """Return a portable, case-normalized cache key path."""
    text = Path(path).as_posix() if not isinstance(path, str) else path.replace("\\", "/")
    parts = [part for part in text.split("/") if part not in {"", "."}]
    return "/".join(parts).lower()


def stable_identity_key(package_path: str, source_path: str | None = None) -> str:
    source_part = normalize_artifact_path(source_path) if source_path else "generated"
    return f"{normalize_artifact_path(package_path)}::{source_part}"


def artifact_id_for(package_path: str, source_path: str | None = None) -> str:
    return deterministic_id("ART", stable_identity_key(package_path, source_path))
