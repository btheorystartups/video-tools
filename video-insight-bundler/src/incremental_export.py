"""Incremental export registries and cache-aware artifact tracking."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from artifact_identity import artifact_id_for, stable_identity_key
from asset_dependency_scanner import classify_file, extract_references, is_text_file, resolve_reference
from dependency_hashing import dependency_hash, metadata_hash, reference_hash, semantic_content_hash
from portable_package_size_report import sha256_file
from stability import deterministic_id, utc_now_iso, write_json


REGISTRY_FILENAMES = {
    "change_graph": "artifact_change_graph.json",
    "incremental_export": "incremental_export_registry.json",
    "incremental_validation": "incremental_validation_registry.json",
    "export_cache": "export_cache_registry.json",
}


def load_previous_cache(package_root: Path) -> dict:
    path = package_root / REGISTRY_FILENAMES["export_cache"]
    if not path.exists():
        return {}
    try:
        cache = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(cache, dict):
            return {}
        if cache.get("storage_format") == "shared_artifact_records_v1":
            records_path = (package_root / cache["artifact_records_file"]).resolve()
            if not records_path.is_relative_to(package_root.resolve()):
                return {}
            graph = json.loads(records_path.read_text(encoding="utf-8"))
            records = graph["artifacts"]
            if len(records) != cache["summary"]["artifact_count"]:
                return {}
            cache["artifacts_by_source"] = {row["source_path"]: row for row in records if row.get("source_path")}
            cache["artifacts_by_package_path"] = {row["package_path"]: row for row in records}
            cache["artifacts_by_identity"] = {row["stable_identity_key"]: row for row in records}
        return cache
    except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError):
        return {}


def write_cache_registry(package_root: Path, cache: dict) -> None:
    """Persist cache indexes by sharing the already-written change graph records."""
    compact = {
        key: value for key, value in cache.items()
        if key not in {"artifacts_by_source", "artifacts_by_package_path", "artifacts_by_identity"}
    }
    compact["storage_format"] = "shared_artifact_records_v1"
    compact["artifact_records_file"] = REGISTRY_FILENAMES["change_graph"]
    write_json(package_root / REGISTRY_FILENAMES["export_cache"], compact)


def hash_source_file(path: Path) -> str:
    return sha256_file(path)


def cached_source_hash(previous_cache: dict, source_abs: str) -> str | None:
    entry = (previous_cache.get("artifacts_by_source") or {}).get(source_abs)
    return entry.get("artifact_hash") if isinstance(entry, dict) else None


def build_reference_edges(package_root: Path) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    upstream: dict[str, set[str]] = defaultdict(set)
    downstream: dict[str, set[str]] = defaultdict(set)
    for path in sorted(package_root.rglob("*"), key=lambda item: item.relative_to(package_root).as_posix().lower()):
        if not path.is_file() or not is_text_file(path):
            continue
        source_rel = path.relative_to(package_root).as_posix()
        for ref in extract_references(path):
            if ref.get("kind") == "absolute_path":
                continue
            resolved = resolve_reference(path, package_root, str(ref.get("value") or ""))
            if not resolved or not resolved.exists() or not resolved.is_file():
                continue
            target_rel = resolved.relative_to(package_root).as_posix()
            if target_rel == source_rel:
                continue
            upstream[source_rel].add(target_rel)
            downstream[target_rel].add(source_rel)
    return (
        {key: sorted(value) for key, value in upstream.items()},
        {key: sorted(value) for key, value in downstream.items()},
    )


def build_incremental_registries(
    package_root: Path,
    *,
    source_root: Path,
    manifest: dict,
    previous_cache: dict | None,
    copied_map: dict[str, str],
    copied_paths: list[str],
    reused_paths: list[str],
    validation_tier: str,
    export_profile: str = "review",
    generation_mode: str = "hybrid",
) -> dict:
    previous_cache = previous_cache or {}
    copied_set = set(copied_paths)
    reused_set = set(reused_paths)
    upstream, downstream = build_reference_edges(package_root)
    previous_by_package = previous_cache.get("artifacts_by_package_path") or {}
    previous_by_source = previous_cache.get("artifacts_by_source") or {}
    now = utc_now_iso()
    artifacts = []
    changed = []
    reused = []
    source_for_package = {package_rel: source_abs for source_abs, package_rel in copied_map.items()}
    for row in sorted(manifest.get("files") or [], key=lambda item: str(item.get("package_path") or "")):
        package_rel = row.get("package_path")
        if not package_rel:
            continue
        package_path = package_root / package_rel
        if not package_path.exists():
            continue
        source_abs = row.get("source_path") or source_for_package.get(package_rel)
        digest = semantic_content_hash(package_path)
        meta_digest = metadata_hash(package_path)
        ref_digest = reference_hash(package_path, package_root)
        dep_digest = dependency_hash(package_path, package_root)
        prev = previous_by_source.get(source_abs) if source_abs else None
        if not isinstance(prev, dict):
            prev = previous_by_package.get(package_rel) if isinstance(previous_by_package.get(package_rel), dict) else {}
        hash_changed = digest != prev.get("artifact_hash")
        copied_now = package_rel in copied_set
        reused_now = package_rel in reused_set or (not copied_now and not hash_changed and bool(prev))
        invalidated = hash_changed or copied_now or not prev
        requires_validation = _requires_validation(package_rel, row, validation_tier, invalidated)
        requires_governance = invalidated and (
            package_rel.endswith((".html", ".htm", ".json"))
            or any(token in package_rel.lower() for token in ("governance", "review", "dashboard", "topology"))
        )
        artifact = {
            "artifact_id": artifact_id_for(package_rel, source_abs),
            "stable_identity_key": stable_identity_key(package_rel, source_abs),
            "artifact_hash": digest,
            "content_hash": digest,
            "metadata_hash": meta_digest,
            "dependency_hash": dep_digest,
            "reference_hash": ref_digest,
            "previous_export_hash": prev.get("content_hash") or prev.get("artifact_hash"),
            "cache_hit": bool(reused_now and not copied_now),
            "cache_miss_reason": None if reused_now and not copied_now else ("content_changed" if prev and hash_changed else "cache_missing"),
            "invalidated_by": [] if reused_now and not copied_now else (["content_changed"] if prev and hash_changed else ["cache_missing"]),
            "reuse_eligible": bool(prev),
            "reuse_decision": "reuse" if reused_now and not copied_now else "refresh",
            "reuse_safety_status": "safe" if reused_now and not copied_now else "refresh_required",
            "generator": row.get("generator") or ("source_analysis_artifact" if source_abs else "portable_export_package"),
            "source_dependencies": [source_abs] if source_abs else [],
            "generated_from": source_abs or "portable_export_package",
            "last_modified": _mtime_iso(package_path),
            "last_exported": now if copied_now or not prev else prev.get("last_exported"),
            "last_validated": now if requires_validation else prev.get("last_validated"),
            "downstream_dependents": downstream.get(package_rel, []),
            "upstream_dependencies": upstream.get(package_rel, []),
            "invalidated": invalidated,
            "changed_since_last_export": hash_changed or copied_now,
            "requires_rewrite": copied_now or package_rel.endswith((".html", ".htm", ".css", ".js")),
            "requires_validation": requires_validation,
            "requires_governance_refresh": requires_governance,
            "package_path": package_rel,
            "source_path": source_abs,
            "artifact_type": row.get("artifact_type") or classify_file(package_root, package_path),
            "cache_status": "reused" if reused_now and not copied_now else "changed",
            "export_profile": export_profile,
            "validation_tier": validation_tier,
            "generation_mode": generation_mode,
        }
        artifacts.append(artifact)
        (changed if artifact["changed_since_last_export"] else reused).append(package_rel)
    change_graph = {
        "analysis_status": "complete",
        "method": "artifact_change_graph_v62",
        "generated_at_utc": now,
        "artifacts": artifacts,
        "edges": [{"source": source, "target": target} for source, targets in upstream.items() for target in targets],
        "summary": {
            "artifact_count": len(artifacts),
            "changed_artifact_count": len(changed),
            "reused_artifact_count": len(reused),
            "invalidated_artifact_count": sum(1 for row in artifacts if row["invalidated"]),
            "requires_rewrite_count": sum(1 for row in artifacts if row["requires_rewrite"]),
            "requires_validation_count": sum(1 for row in artifacts if row["requires_validation"]),
            "requires_governance_refresh_count": sum(1 for row in artifacts if row["requires_governance_refresh"]),
        },
    }
    export_registry = {
        "analysis_status": "complete",
        "method": "incremental_export_registry_v62",
        "generated_at_utc": now,
        "cache_mode": "incremental",
        "changed_artifacts": changed,
        "reused_artifacts": reused,
        "partial_rewrite_supported": True,
        "partial_validation_supported": True,
        "incremental_governance_supported": True,
        "incremental_zip_supported": True,
        "summary": change_graph["summary"],
    }
    validation_registry = {
        "analysis_status": "complete",
        "method": "incremental_validation_registry_v62",
        "generated_at_utc": now,
        "validation_tier": validation_tier,
        "validated_artifacts": [row["package_path"] for row in artifacts if row["requires_validation"]],
        "skipped_unchanged_artifacts": [row["package_path"] for row in artifacts if not row["requires_validation"]],
        "summary": {
            "validation_tier": validation_tier,
            "validated_artifact_count": sum(1 for row in artifacts if row["requires_validation"]),
            "skipped_unchanged_artifact_count": sum(1 for row in artifacts if not row["requires_validation"]),
        },
    }
    cache = {
        "analysis_status": "complete",
        "method": "export_cache_registry_v62",
        "generated_at_utc": now,
        "source_analysis_root": source_root.as_posix(),
        "artifacts_by_source": {row["source_path"]: row for row in artifacts if row.get("source_path")},
        "artifacts_by_package_path": {row["package_path"]: row for row in artifacts},
        "artifacts_by_identity": {row["stable_identity_key"]: row for row in artifacts},
        "summary": change_graph["summary"],
    }
    write_json(package_root / REGISTRY_FILENAMES["change_graph"], change_graph)
    write_json(package_root / REGISTRY_FILENAMES["incremental_export"], export_registry)
    write_json(package_root / REGISTRY_FILENAMES["incremental_validation"], validation_registry)
    write_cache_registry(package_root, cache)
    return {
        "artifact_change_graph": change_graph,
        "incremental_export_registry": export_registry,
        "incremental_validation_registry": validation_registry,
        "export_cache_registry": cache,
    }


def write_performance_comparison(package_root: Path, timings: dict, incremental: dict, previous_cache: dict | None) -> dict:
    summary = incremental.get("incremental_export_registry", {}).get("summary", {})
    total = timings.get("total_duration_seconds") or 0
    changed = summary.get("changed_artifact_count") or 0
    reused = summary.get("reused_artifact_count") or 0
    artifact_count = max(summary.get("artifact_count") or changed + reused, 1)
    estimated_uncached = round(total / max((changed / artifact_count), 0.1), 4) if total else None
    report = {
        "analysis_status": "complete",
        "method": "incremental_performance_comparison_v62",
        "generated_at_utc": utc_now_iso(),
        "baseline": {"label": "V61 estimated full export", "duration_seconds": estimated_uncached},
        "current": {"label": "V62+ export", "duration_seconds": total},
        "cached_export_timings": timings if previous_cache else {},
        "uncached_export_timings": timings if not previous_cache else {"estimated_uncached_total_seconds": estimated_uncached},
        "summary": {
            "cache_available": bool(previous_cache),
            "changed_artifact_count": changed,
            "reused_artifact_count": reused,
            "reuse_ratio": round(reused / artifact_count, 4),
            "estimated_seconds_saved": round(max((estimated_uncached or total) - total, 0), 4) if total else 0,
        },
    }
    write_json(package_root / "incremental_performance_comparison.json", report)
    write_json(package_root / "validation" / "incremental_performance_comparison.json", report)
    return report


def _requires_validation(package_rel: str, row: dict, tier: str, invalidated: bool) -> bool:
    if tier == "quick":
        return invalidated
    if tier == "standard":
        return invalidated or package_rel in {"index.html", "portable_package_manifest.json"}
    if tier == "strict":
        return invalidated or row.get("artifact_type") in {"dashboard", "manifest", "schema"} or "governance" in package_rel.lower()
    if tier == "extracted_full":
        return True
    return invalidated


def _mtime_iso(path: Path) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
