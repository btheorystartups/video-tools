"""V67 incremental cache optimization reports."""

from __future__ import annotations

from pathlib import Path

from artifact_identity import artifact_id_for, stable_identity_key
from cache_invalidation_policy import decide_reuse, write_cache_invalidation_report
from dependency_hashing import build_dependency_hash_registry
from portable_package_size_report import sha256_file
from stability import utc_now_iso, write_json


def build_incremental_cache_optimization(
    package_root: Path,
    *,
    manifest: dict,
    previous_cache: dict | None,
    export_profile: str,
    validation_tier: str,
    generation_mode: str,
    cache_mode: str = "auto",
) -> dict:
    dependency_registry = build_dependency_hash_registry(package_root)
    previous_by_identity = (previous_cache or {}).get("artifacts_by_identity") or {}
    previous_by_package = (previous_cache or {}).get("artifacts_by_package_path") or {}
    hashes = {row["package_path"]: row for row in dependency_registry["artifacts"]}
    artifacts = []
    for row in sorted(manifest.get("files") or [], key=lambda item: str(item.get("package_path") or "")):
        package_rel = row.get("package_path")
        if not package_rel:
            continue
        path = package_root / package_rel
        if not path.exists():
            continue
        source_path = row.get("source_path")
        current_hashes = hashes.get(package_rel) or {}
        identity_key = stable_identity_key(package_rel, source_path)
        previous = previous_by_identity.get(identity_key) or previous_by_package.get(package_rel)
        current = {
            "artifact_id": artifact_id_for(package_rel, source_path),
            "stable_identity_key": identity_key,
            "package_path": package_rel,
            "source_path": source_path,
            "artifact_type": row.get("artifact_type"),
            "content_hash": current_hashes.get("content_hash") or sha256_file(path),
            "metadata_hash": current_hashes.get("metadata_hash"),
            "dependency_hash": current_hashes.get("dependency_hash"),
            "reference_hash": current_hashes.get("reference_hash"),
            "previous_export_hash": previous.get("content_hash") or previous.get("artifact_hash") if isinstance(previous, dict) else None,
            "export_profile": export_profile,
            "validation_tier": validation_tier,
            "generation_mode": generation_mode,
        }
        current.update(
            decide_reuse(
                current=current,
                previous=previous if isinstance(previous, dict) else None,
                export_profile=export_profile,
                validation_tier=validation_tier,
                generation_mode=generation_mode,
                cache_mode=cache_mode,
                source_exists=not source_path or Path(source_path).exists(),
            )
        )
        artifacts.append(current)
    registry = {
        "analysis_status": "complete",
        "method": "artifact_identity_registry_v67",
        "generated_at_utc": utc_now_iso(),
        "artifacts": artifacts,
        "summary": {"artifact_count": len(artifacts), "stable_identity_count": len({row["stable_identity_key"] for row in artifacts})},
    }
    report = {
        "analysis_status": "complete",
        "method": "incremental_cache_optimizer_v67",
        "generated_at_utc": utc_now_iso(),
        "cache_mode": cache_mode,
        "reuse_ratio": round(sum(1 for row in artifacts if row["cache_hit"]) / max(len(artifacts), 1), 4),
        "artifacts": artifacts,
        "summary": {
            "artifact_count": len(artifacts),
            "cache_hit_count": sum(1 for row in artifacts if row["cache_hit"]),
            "cache_miss_count": sum(1 for row in artifacts if not row["cache_hit"]),
            "reuse_eligible_count": sum(1 for row in artifacts if row["reuse_eligible"]),
        },
    }
    invalidation = write_cache_invalidation_report(package_root, artifacts)
    write_json(package_root / "artifact_identity_registry.json", registry)
    write_json(package_root / "validation" / "artifact_identity_registry.json", registry)
    write_json(package_root / "incremental_cache_optimization_report.json", report)
    write_json(package_root / "validation" / "incremental_cache_optimization_report.json", report)
    return {
        "incremental_cache_optimization_report": report,
        "cache_invalidation_report": invalidation,
        "artifact_identity_registry": registry,
        "dependency_hash_registry": dependency_registry,
    }
