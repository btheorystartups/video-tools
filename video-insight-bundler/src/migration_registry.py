"""Non-destructive migration registry scaffolding."""

from __future__ import annotations

from pathlib import Path

from artifact_versioning import build_artifact_versions
from stability import STATUS_COMPLETE, utc_now_iso, write_json


def build_migration_registry(output_dir: Path, schema_dir: Path) -> dict:
    versions = build_artifact_versions(schema_dir)
    registry = {
        "validation_status": STATUS_COMPLETE,
        "generated_at_utc": utc_now_iso(),
        "migration_registry_version": "1.0",
        "artifact_versions": versions.get("artifact_versions", {}),
        "schema_versions": {key: value.get("schema_version") for key, value in versions.get("artifact_versions", {}).items()},
        "compatibility_notes": versions.get("compatibility_policy", {}),
        "migration_placeholders": [
            {
                "from_version": "1.0",
                "to_version": "1.x",
                "migration_type": "additive_metadata_only",
                "destructive": False,
                "status": "placeholder",
            }
        ],
        "deprecated_fields": [],
        "future_migration_hooks": [
            "register_artifact_schema_version",
            "validate_backward_compatible_addition",
            "map_deprecated_field_to_replacement",
            "write_non_destructive_migration_report",
        ],
        "limitations": [
            "Registry declares compatibility metadata only; it does not rewrite existing artifacts.",
            "Destructive migrations are intentionally unsupported.",
        ],
    }
    integrity = Path(output_dir) / "integrity"
    integrity.mkdir(exist_ok=True)
    write_json(integrity / "migration_registry.json", registry)
    return registry


def write_migration_report(output_dir: Path, registry: dict) -> None:
    reports = Path(output_dir) / "reports"
    reports.mkdir(exist_ok=True)
    lines = [
        "# Migration Registry Report",
        "",
        f"- Registry version: `{registry.get('migration_registry_version')}`",
        f"- Versioned artifacts: `{len(registry.get('artifact_versions') or {})}`",
        "- Destructive migrations: `unsupported`",
        "",
        "## Future Hooks",
        "",
    ]
    lines.extend(f"- `{hook}`" for hook in registry.get("future_migration_hooks", []))
    (reports / "migration_registry_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
