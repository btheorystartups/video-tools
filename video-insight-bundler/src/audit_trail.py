"""Corpus audit trail generation."""

from __future__ import annotations

from pathlib import Path

from intelligence_common import base_artifact, deterministic_id, read_json
from stability import sha256_text, write_json


def _hash_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return sha256_text(path.read_text(encoding="utf-8", errors="replace"))


def build_audit_trail(corpus_output_dir: Path, analysis_dirs: list[Path], command: list[str], run_manifest: dict) -> dict:
    entries = []
    for analysis_dir in analysis_dirs:
        manifest = read_json(analysis_dir / "manifest.json")
        artifacts = sorted(path for path in analysis_dir.rglob("*") if path.is_file() and path.suffix.lower() in {".json", ".md", ".html", ".png", ".csv", ".srt"})
        entries.append(
            {
                "audit_entry_id": deterministic_id("AUD", str(analysis_dir), manifest.get("source_video_sha256")),
                "source_video": manifest.get("source_video"),
                "source_video_hash": manifest.get("source_video_sha256"),
                "analysis_dir": str(analysis_dir),
                "analysis_command": command,
                "profile_hash": manifest.get("analysis_profile_hash"),
                "dependency_versions": manifest.get("dependency_versions", {}),
                "schema_validation_status": manifest.get("schema_validation_status"),
                "validation_statuses": manifest.get("subsystem_statuses", {}),
                "generated_artifact_hashes": {
                    path.relative_to(analysis_dir).as_posix(): _hash_file(path)
                    for path in artifacts[:500]
                },
                "warnings": manifest.get("warnings", []),
                "limitations": manifest.get("limitations", []),
                "non_mutation_statement": "Corpus audit records generated artifacts only; no source media, timeline, Resolve project, cloud service, LLM, embedding store, or vector database is mutated or called.",
            }
        )
    output = base_artifact(method="deterministic_corpus_audit_trail_v1")
    output.update(
        {
            "audit_trail_id": deterministic_id("AUDIT", [row.get("audit_entry_id") for row in entries]),
            "corpus_run_manifest_ref": "corpus/corpus_run_manifest.json",
            "audit_entries": entries,
            "summary": {
                "analysis_count": len(entries),
                "warning_count": sum(len(row.get("warnings") or []) for row in entries),
                "failed_video_count": len(run_manifest.get("failed_videos") or []),
                "audit_completeness_score": 1.0 if entries else 0.0,
            },
        }
    )
    write_json(corpus_output_dir / "audit" / "audit_trail.json", output)
    return output
