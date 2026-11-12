"""Lightweight historical run snapshots for local drift comparison."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from dependency_diagnostics import dependency_versions
from schema_validation import validate_against_schema
from stability import TOOL_VERSION, canonical_json, deterministic_id, utc_now_iso, write_json

HISTORY_ARTIFACTS = {
    "run_history": "history/run_history.json",
    "run_snapshots": "history/run_snapshots.json",
}

VOLATILE_KEYS = {
    "generated_at_utc",
    "run_timestamp_utc",
    "timestamp",
    "execution_duration_sec",
    "duration_sec",
}


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _strip_volatile(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _strip_volatile(v) for k, v in value.items() if k not in VOLATILE_KEYS}
    if isinstance(value, list):
        return [_strip_volatile(item) for item in value]
    return value


def stable_artifact_hash(path: Path) -> str | None:
    if path.suffix.lower() == ".json":
        data = read_json(path)
        if data:
            return hashlib.sha256(canonical_json(_strip_volatile(data)).encode("utf-8")).hexdigest()
    return file_sha256(path)


def _schema_versions(root: Path) -> dict:
    versions = {}
    for path in sorted(root.glob("**/*.json")):
        if "history" in path.parts:
            continue
        data = read_json(path)
        if not data:
            continue
        rel = path.relative_to(root).as_posix()
        version = data.get("schema_version") or data.get("report_version") or data.get("version")
        if version is not None:
            versions[rel] = str(version)
    return versions


def _artifact_hashes(root: Path) -> dict:
    hashes = {}
    for path in sorted(root.glob("**/*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith(("frames/", "history/")) or rel == "analysis_audio.wav":
            continue
        digest = stable_artifact_hash(path)
        if digest:
            hashes[rel] = digest
    return hashes


def build_run_snapshot(bundle, manifest: dict, analysis_index: dict | None = None) -> dict:
    root = Path(bundle.output_dir)
    index = analysis_index or read_json(root / "analysis_index.json")
    readiness = read_json(root / "revision_graph" / "release_readiness_report.json")
    recommendations = read_json(root / "recommendations.json")
    integrity = read_json(root / "integrity" / "artifact_integrity.json")
    source_sha = bundle.media_metadata.get("sha256")
    profile_hash = bundle.profile_hash
    run_id = deterministic_id("run", source_sha, profile_hash, TOOL_VERSION, length=20)
    return {
        "snapshot_schema_version": "1.0",
        "run_id": run_id,
        "timestamp_utc": utc_now_iso(),
        "source_video": bundle.source_video,
        "source_sha256": source_sha,
        "profile_hash": profile_hash,
        "tool_version": TOOL_VERSION,
        "dependency_versions": dependency_versions(bundle.dependency_report),
        "schema_versions": _schema_versions(root),
        "artifact_hashes": _artifact_hashes(root),
        "key_metrics": index.get("key_metrics", {}),
        "readiness": {
            "score": readiness.get("release_readiness_score"),
            "class": readiness.get("release_readiness_class"),
        },
        "warning_count": len(manifest.get("warnings") or []),
        "recommendation_count": len(recommendations.get("recommendations") or []),
        "integrity_scores": {
            "artifact_integrity_score": integrity.get("integrity_score"),
            **(manifest.get("integrity_summary") or {}),
        },
    }


def load_snapshots(root: Path) -> list[dict]:
    data = read_json(root / "history" / "run_snapshots.json")
    return list(data.get("snapshots") or [])


def write_run_history(root: Path, snapshot: dict, previous: list[dict], schema_dir: Path) -> dict:
    history_dir = root / "history"
    history_dir.mkdir(exist_ok=True)
    snapshots = list(previous)
    snapshots.append(snapshot)
    snapshots = snapshots[-20:]
    history = {
        "history_schema_version": "1.0",
        "generated_at_utc": utc_now_iso(),
        "source_sha256": snapshot.get("source_sha256"),
        "latest_run_id": snapshot.get("run_id"),
        "snapshot_count": len(snapshots),
        "runs": [
            {
                "run_id": row.get("run_id"),
                "timestamp_utc": row.get("timestamp_utc"),
                "source_sha256": row.get("source_sha256"),
                "profile_hash": row.get("profile_hash"),
                "readiness_score": (row.get("readiness") or {}).get("score"),
                "readiness_class": (row.get("readiness") or {}).get("class"),
            }
            for row in snapshots
        ],
    }
    snapshots_doc = {"snapshots_schema_version": "1.0", "snapshots": snapshots}
    write_json(history_dir / "run_history.json", history)
    write_json(history_dir / "run_snapshots.json", snapshots_doc)
    existing = read_json(root / "verification_evidence" / "history_validation.json")
    validations = list(existing.get("validations") or [])
    validations.append(validate_against_schema(history, schema_dir / "run_history.schema.json"))
    evidence = {
        "validation_status": "complete",
        "generated_at_utc": utc_now_iso(),
        "validations": validations,
    }
    evidence["validation_status"] = "complete" if all(row.get("validation_status") == "complete" for row in evidence["validations"]) else "error"
    write_json(root / "verification_evidence" / "history_validation.json", evidence)
    return history
