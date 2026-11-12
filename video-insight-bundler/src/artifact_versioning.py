"""Artifact schema version inventory and compatibility metadata."""

from __future__ import annotations

import json
from pathlib import Path

from stability import TOOL_VERSION

DEFAULT_ARTIFACT_VERSION = "1.0"


def _schema_title(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("title") or path.stem
    except Exception:
        return path.stem


def build_artifact_versions(schema_dir: Path) -> dict:
    schemas = {}
    for path in sorted(Path(schema_dir).glob("*.schema.json")):
        name = path.name
        artifact_name = name.replace(".schema.json", ".json")
        schemas[artifact_name] = {
            "artifact_version": DEFAULT_ARTIFACT_VERSION,
            "schema_version": DEFAULT_ARTIFACT_VERSION,
            "schema_file": name,
            "schema_title": _schema_title(path),
            "compatibility": "backward_compatible_additive_fields",
        }
    return {
        "tool_version": TOOL_VERSION,
        "default_artifact_version": DEFAULT_ARTIFACT_VERSION,
        "artifact_versions": schemas,
        "compatibility_policy": {
            "additive_fields": "allowed",
            "field_removal": "requires migration placeholder and deprecation note",
            "type_changes": "requires explicit migration hook",
            "destructive_migrations": "not supported by this local-first analyzer",
        },
    }
