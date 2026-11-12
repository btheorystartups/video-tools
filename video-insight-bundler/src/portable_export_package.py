"""Build self-contained portable review packages from Corpus_analysis outputs."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import sys
import tempfile
import time
import zipfile
from collections import Counter
from pathlib import Path

from artifact_lifecycle_compaction import build_lazy_generation_registry, build_lifecycle_compaction
from artifact_reduction_engine import build_artifact_reduction_report
from asset_dependency_scanner import IMAGE_EXTENSIONS, TEXT_EXTENSIONS, classify_file, extract_references, resolve_reference, scan_asset_dependencies
from change_intelligence_engine import build_change_intelligence
from executive_synthesis_engine import build_executive_synthesis
from historical_continuity import build_historical_continuity
from incremental_export import build_incremental_registries, cached_source_hash, hash_source_file, load_previous_cache, write_performance_comparison
from incremental_cache_optimizer import build_incremental_cache_optimization
from incremental_zip_packaging import build_delta_zip, build_zip_file
from longitudinal_summary_engine import build_longitudinal_summary
from offline_dashboard_hardening import harden_offline_dashboards
from pre_rc_readiness_review import build_pre_rc_readiness_review
from portable_cleanup import clean_old_exports
from portable_dashboard_governance import build_dashboard_governance, validate_dashboard_governance
from portable_exclusion_policy import EXPORT_PROFILES, RAW_MEDIA_EXTENSIONS, build_exclusion_entry, is_privacy_risky, is_raw_media, should_exclude_path
from portable_integrity_checker import check_portable_integrity
from portable_metadata_compaction import compact_package_metadata
from portable_demo_readiness import audit_fallback_links, build_demo_walkthrough
from portable_package_diff import write_diff_report
from portable_package_size_report import sha256_file, write_size_report
from portable_package_validator import validate_portable_package
from portable_reachability import analyze_reachability, write_export_audit_report
from review_session_workflows import build_review_sessions, render_review_session_index
from review_ux_controls import build_review_ux_registries
from reviewer_workspace import build_reviewer_workspace
from review_navigation_policy import is_analytical_review_target
from stability import deterministic_id, utc_now_iso, write_json
from synthetic_dashboard_generator import build_synthetic_dashboards
from topology_graph_engine import build_topology_graph
from topology_simplifier import simplify_topology

PACKAGE_DIRNAME = "portable_review_package"
PACKAGE_VERSION = "v58_portable_package_v1"
MAX_PACKAGE_REL_PATH_CHARS = 112
MAX_PACKAGE_PART_CHARS = 72
DEDUPE_DISPLAY_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".css", ".js"}
EXTERNAL_DISPLAY_EXTENSIONS = IMAGE_EXTENSIONS | {".css", ".js"}

PROFILE_USE_CASES = {
    "minimal": "Smallest practical package for quick offline orientation.",
    "review": "Default package for human analytical review and recommendation inspection.",
    "audit": "Review package plus provenance, validation, replay, diff, lineage, schema, and manifest evidence.",
    "full": "Broadest non-video generated artifact package, excluding caches, secrets, temp files, and prior packages.",
    "executive": "Compact nontechnical package focused on summary, findings, recommendations, and readiness.",
    "presentation": "Visual-first package for sharing dashboards, graphs, and concise summaries externally.",
    "investigation": "Focused evidence, recommendation, timeline, governance, interpretation, and validation package.",
    "diff_only": "Delta, snapshot, replay, and regression package with enough navigation to inspect changes.",
}

PROFILE_EXCLUSIONS = {
    "minimal": "Deep audit artifacts, low-level registries, schemas, provenance, replay, snapshots, noisy machine JSON, and raw media.",
    "review": "Low-level machine/audit JSON, schemas, raw media, caches, temp files, secrets, and old packages.",
    "audit": "Raw video by default, caches, temp files, secrets, and old packages.",
    "full": "Raw video unless explicitly requested, caches, temp files, secrets, and old packages.",
    "executive": "Detailed audit/provenance artifacts, schemas, replay, snapshots, low-level JSON, and raw media.",
    "presentation": "Most machine JSON, schemas, provenance, replay, snapshots, and raw media.",
    "investigation": "Noisy debug artifacts, unrelated display assets, unrelated machine JSON, and raw media.",
    "diff_only": "Non-diff/non-regression artifacts, broad dashboards, unrelated summaries, and raw media.",
}


def _rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _category_target(source_root: Path, path: Path, include_raw_media: bool = False) -> Path:
    rel = path.relative_to(source_root)
    lower = rel.as_posix().lower()
    suffix = path.suffix.lower()
    if is_raw_media(path) and include_raw_media:
        return Path("media") / rel.name
    if rel.parts and rel.parts[0] in {
        "visualizations",
        "graphs",
        "reports",
        "schemas",
        "verification_evidence",
        "static_assets",
        "timeline",
        "recommendations",
        "governance",
        "review_sessions",
        "review_input",
        "templates",
        "queues",
        "evidence",
        "snapshots",
        "diffs",
        "replay",
        "llm_interpretation",
        "interpretation_packets",
        "graph_ux",
        "workbench",
        "audit",
        "corpus",
    }:
        return rel
    if len(rel.parts) > 1:
        return rel
    if suffix in {".html", ".htm"}:
        return Path("dashboards") / rel.name
    if suffix in IMAGE_EXTENSIONS:
        if "graph" in lower:
            return Path("graphs") / rel.name
        if "storyboard" in lower:
            return Path("storyboards") / rel.name
        if any(token in lower for token in ("inspection", "delta", "board", "contact_sheet")):
            return Path("boards") / rel.name
        return Path("images") / rel.name
    if suffix == ".json":
        if "schema" in lower:
            return Path("schemas") / rel.name
        if "manifest" in lower:
            return Path("manifests") / rel.name
        if "workflow" in lower:
            return Path("workflows") / rel.name
        if "timeline" in lower:
            return Path("timelines") / rel.name
        if "evidence" in lower:
            return Path("evidence") / rel.name
        return Path("json") / rel.name
    if suffix == ".md":
        return Path("markdown") / rel.name
    if suffix in {".csv", ".tsv"}:
        return Path("review") / rel.name
    if "log" in lower or suffix == ".txt":
        return Path("logs") / rel.name
    return rel


def _safe_name(name: str, *, max_chars: int = MAX_PACKAGE_PART_CHARS) -> str:
    safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in name)
    if len(safe) <= max_chars:
        return safe
    suffix = Path(safe).suffix
    stem_limit = max(16, max_chars - len(suffix))
    return f"{Path(safe).stem[:stem_limit]}{suffix}"


def _short_bucket(path: Path) -> str:
    lower = path.as_posix().lower()
    if "schema" in lower:
        return "schemas/short"
    if "snapshot" in lower:
        return "snapshots/short"
    if "replay" in lower:
        return "replay/short"
    if "diff" in lower or "delta" in lower:
        return "diffs/short"
    if "validation" in lower or "verification" in lower:
        return "validation/short"
    if "manifest" in lower:
        return "manifests/short"
    return "artifacts/short"


def _shorten_target_rel(target_rel: Path, source_path: Path) -> Path:
    rel_text = target_rel.as_posix()
    if len(rel_text) <= MAX_PACKAGE_REL_PATH_CHARS and all(len(part) <= MAX_PACKAGE_PART_CHARS for part in target_rel.parts):
        return Path(*(_safe_name(part) for part in target_rel.parts))
    digest = hashlib.sha256(source_path.resolve().as_posix().encode("utf-8")).hexdigest()[:12]
    filename = _safe_name(source_path.name, max_chars=64)
    return Path(_short_bucket(target_rel)) / f"{digest}_{filename}"


def _prepare_dirs(package_root: Path) -> None:
    for dirname in [
        "dashboards",
        "pages",
        "graphs",
        "images",
        "boards",
        "storyboards",
        "inspection",
        "cinematic",
        "json",
        "markdown",
        "reports",
        "manifests",
        "schemas",
        "workflows",
        "timelines",
        "evidence",
        "recommendations",
        "governance",
        "review",
        "review_notes",
        "interpretations",
        "validation",
        "provenance",
        "snapshots",
        "diffs",
        "replay",
        "assets/css",
        "assets/js",
        "assets/images",
        "assets/fonts",
        "logs",
    ]:
        (package_root / dirname).mkdir(parents=True, exist_ok=True)


def _copy_tree(
    source_root: Path,
    package_root: Path,
    include_raw_media: bool,
    export_profile: str,
    previous_cache: dict | None = None,
) -> tuple[dict[str, str], list[dict], dict]:
    copied: dict[str, str] = {}
    exclusions: list[dict] = []
    stats = {"copied_paths": [], "reused_paths": [], "changed_source_count": 0, "reused_source_count": 0}
    ignored_names = {PACKAGE_DIRNAME, f"{PACKAGE_DIRNAME}.zip"}
    for path in sorted(source_root.rglob("*"), key=lambda item: item.as_posix().lower()):
        if not path.is_file():
            continue
        rel = path.relative_to(source_root)
        if rel.parts and rel.parts[0] in ignored_names:
            continue
        if path.name in ignored_names:
            continue
        exclude, reason, rule = should_exclude_path(path, source_root, include_raw_media=include_raw_media, export_profile=export_profile)
        if exclude:
            exclusions.append(build_exclusion_entry(path, source_root, reason, rule))
            continue
        target_rel = _shorten_target_rel(_category_target(source_root, path, include_raw_media=include_raw_media), path)
        target = package_root / target_rel
        source_abs = path.resolve().as_posix()
        previous_entry = ((previous_cache or {}).get("artifacts_by_source") or {}).get(source_abs) or {}
        previous_target = previous_entry.get("package_path") if isinstance(previous_entry, dict) else None
        if target.exists() and previous_target != target_rel.as_posix():
            digest = hashlib.sha256(rel.as_posix().encode("utf-8")).hexdigest()[:8]
            target = target.with_name(f"{target.stem}_{digest}{target.suffix}")
            target_rel = target.relative_to(package_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        source_hash = hash_source_file(path)
        cached_hash = cached_source_hash(previous_cache or {}, source_abs)
        if target.exists() and cached_hash == source_hash:
            stats["reused_paths"].append(target_rel.as_posix())
            stats["reused_source_count"] += 1
        else:
            shutil.copy2(path, target)
            stats["copied_paths"].append(target_rel.as_posix())
            stats["changed_source_count"] += 1
        copied[path.resolve().as_posix()] = target_rel.as_posix()
    return copied, exclusions, stats


def _copy_external_display_assets(source_root: Path, package_root: Path, copied_map: dict[str, str], include_raw_media: bool, export_profile: str) -> list[dict]:
    copied_external: list[dict] = []
    reverse_map = {package_rel: source_abs for source_abs, package_rel in copied_map.items()}
    for package_file in sorted(package_root.rglob("*"), key=lambda item: item.relative_to(package_root).as_posix().lower()):
        if not package_file.is_file() or package_file.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        package_rel = package_file.relative_to(package_root).as_posix()
        original_source = reverse_map.get(package_rel)
        if not original_source:
            continue
        original_file = Path(original_source)
        for ref in extract_references(package_file):
            value = str(ref.get("value") or "")
            resolved = resolve_reference(original_file, source_root, value)
            if not resolved or not resolved.is_file():
                continue
            resolved_key = resolved.resolve().as_posix()
            if resolved_key in copied_map:
                copied_map[value] = copied_map[resolved_key]
                copied_map[value.replace("\\", "/")] = copied_map[resolved_key]
                continue
            if resolved.suffix.lower() not in EXTERNAL_DISPLAY_EXTENSIONS:
                continue
            exclude, _reason, _rule = should_exclude_path(resolved, source_root, include_raw_media=include_raw_media, export_profile=export_profile)
            if exclude:
                continue
            subdir = "css" if resolved.suffix.lower() == ".css" else "js" if resolved.suffix.lower() == ".js" else "images/external"
            digest = hashlib.sha256(resolved_key.encode("utf-8")).hexdigest()[:12]
            target_rel = Path("assets") / subdir / f"{digest}_{_safe_name(resolved.name, max_chars=64)}"
            target = package_root / target_rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(resolved, target)
            copied_map[resolved_key] = target_rel.as_posix()
            copied_map[value] = target_rel.as_posix()
            copied_map[value.replace("\\", "/")] = target_rel.as_posix()
            copied_external.append(
                {
                    "source_path": resolved_key,
                    "package_path": target_rel.as_posix(),
                    "referenced_by": package_rel,
                    "reference_type": ref.get("kind"),
                }
            )
    if copied_external:
        write_json(
            package_root / "manifests" / "external_display_assets_copied.json",
            {
                "analysis_status": "complete",
                "method": "external_display_asset_copy_v1",
                "generated_at_utc": utc_now_iso(),
                "copied_external_display_asset_count": len(copied_external),
                "copied_external_display_assets": copied_external,
            },
        )
    return copied_external


def _copy_external_assets(source_root: Path, package_root: Path, scan: dict, copied_map: dict[str, str], exclusions: list[dict], include_raw_media: bool, export_profile: str) -> None:
    linked_dir = package_root / "evidence" / "linked_assets"
    for row in scan.get("references", []):
        resolved = row.get("resolved_path")
        if not resolved:
            continue
        source = Path(resolved)
        if not source.exists() or not source.is_file() or source.resolve().as_posix() in copied_map:
            continue
        exclude, reason, rule = should_exclude_path(source, source_root, include_raw_media=include_raw_media, export_profile=export_profile)
        if exclude:
            exclusions.append(build_exclusion_entry(source, source_root if source.is_relative_to(source_root) else source.parent, reason, rule))
            continue
        target = linked_dir / source.name
        if target.exists():
            digest = hashlib.sha256(source.resolve().as_posix().encode("utf-8")).hexdigest()[:8]
            target = linked_dir / f"{source.stem}_{digest}{source.suffix}"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied_map[source.resolve().as_posix()] = target.relative_to(package_root).as_posix()


def _write_exclusion_manifest(package_root: Path, exclusions: list[dict]) -> dict:
    report = {
        "analysis_status": "complete",
        "method": "portable_exclusion_manifest_v1",
        "generated_at_utc": utc_now_iso(),
        "summary": {
            "excluded_file_count": len(exclusions),
            "raw_media_excluded_count": sum(1 for row in exclusions if "raw_" in str(row.get("matched_rule"))),
            "privacy_risky_file_count": sum(1 for row in exclusions if "privacy" in str(row.get("matched_rule"))),
            "excluded_bytes": sum(row.get("file_size_bytes", 0) for row in exclusions),
        },
        "excluded_files": exclusions,
    }
    write_json(package_root / "exclusion_manifest.json", report)
    write_json(package_root / "manifests" / "exclusion_manifest.json", report)
    return report


def _write_privacy_scan(package_root: Path, exclusions: list[dict]) -> dict:
    risky_copied = [path.relative_to(package_root).as_posix() for path in package_root.rglob("*") if path.is_file() and is_privacy_risky(path)]
    risky_excluded = [row for row in exclusions if "privacy" in str(row.get("matched_rule")) or is_privacy_risky(Path(row.get("source_path", "")))]
    report = {
        "analysis_status": "complete" if not risky_copied else "error",
        "method": "portable_privacy_scan_v1",
        "generated_at_utc": utc_now_iso(),
        "summary": {
            "risky_file_count": len(risky_copied) + len(risky_excluded),
            "risky_copied_count": len(risky_copied),
            "risky_excluded_count": len(risky_excluded),
        },
        "risky_copied_files": risky_copied,
        "risky_excluded_files": risky_excluded,
    }
    write_json(package_root / "validation" / "portable_privacy_scan_report.json", report)
    return report


def _artifact_flags(asset_type: str, rel: str) -> tuple[bool, bool, bool]:
    display = asset_type in {"dashboard", "html", "graph", "board", "image", "web_asset"}
    analysis = asset_type in {"json", "markdown", "manifest", "schema", "interpretation", "recommendation", "evidence", "governance", "timeline", "snapshot", "diff", "replay", "review_sheet"}
    validation = "validation" in rel.lower() or asset_type == "schema"
    return display, analysis, validation


def _human_review_value(asset_type: str, rel: str) -> str:
    lower = rel.lower()
    if asset_type in {"dashboard", "html", "graph", "board", "markdown", "recommendation", "evidence", "governance"}:
        return "high"
    if asset_type in {"interpretation", "timeline", "manifest"} or any(token in lower for token in ("summary", "readiness", "validation")):
        return "medium"
    return "low"


def _profile_reason(asset_type: str, rel: str, export_profile: str) -> str:
    if export_profile in {"full", "audit"}:
        return f"Included by {export_profile} profile for broad inspection."
    if asset_type in {"dashboard", "html", "graph", "board", "image", "web_asset"}:
        return "Included for offline dashboard display."
    if _human_review_value(asset_type, rel) in {"high", "medium"}:
        return "Included for human review."
    return f"Included by {export_profile} profile policy."


def _build_file_manifest(source_root: Path, package_root: Path, copied_map: dict[str, str], package_scan: dict, export_profile: str) -> list[dict]:
    referenced_by = {}
    for ref in package_scan.get("references", []):
        target = ref.get("resolved_relative_path")
        if target:
            referenced_by.setdefault(target, []).append({"source": ref.get("source"), "reference_type": ref.get("kind"), "value": ref.get("value")})
    rows = []
    seen_package_paths = set()
    for source_abs, package_rel in sorted(copied_map.items(), key=lambda item: item[1].lower()):
        if package_rel in seen_package_paths:
            continue
        seen_package_paths.add(package_rel)
        package_path = package_root / package_rel
        if not package_path.exists():
            continue
        source_path = Path(source_abs)
        artifact_type = classify_file(source_root if source_path.is_relative_to(source_root) else source_path.parent, source_path)
        display, analysis, validation = _artifact_flags(artifact_type, package_rel)
        refs = referenced_by.get(package_rel, [])
        human_value = _human_review_value(artifact_type, package_rel)
        rows.append(
            {
                "source_path": source_abs,
                "package_path": package_rel,
                "relative_path_from_index": package_rel,
                "artifact_type": artifact_type,
                "profile_inclusion": export_profile,
                "inclusion_reason": _profile_reason(artifact_type, package_rel, export_profile),
                "human_review_value": human_value,
                "linked_from_entrypoint": bool(refs),
                "reachable_from_dashboard": bool(refs),
                "required_for_offline_display": display,
                "required_for_analysis_inspection": analysis,
                "required_for_audit": export_profile in {"audit", "full"} or artifact_type in {"manifest", "schema", "snapshot", "diff", "replay"},
                "required_for_validation": validation,
                "size_bytes": package_path.stat().st_size,
                "sha256": sha256_file(package_path),
                "dedupe_group_id": None,
                "rewrite_status": "rewritten_or_checked",
                "validation_status": "pending",
                "copied": True,
                "referenced_by": refs,
                "is_entrypoint": package_rel in {"index.html", "visualizations/dashboard.html", "visualizations/corpus_dashboard.html"},
                "is_required_for_display": display,
                "is_required_for_analysis": analysis,
                "is_required_for_validation": validation,
            }
        )
    return rows


def _append_generated_manifest_entries(package_root: Path, manifest: dict) -> None:
    known = {row.get("package_path") for row in manifest.get("files", [])}
    generated_roots = {
        "index.html",
        "PACKAGE_SUMMARY.md",
        "portable_package_manifest.json",
        "portable_package_validation_report.json",
        "package_diff_report.json",
        "package_size_report.json",
        "exclusion_manifest.json",
        "raw_media_excluded.html",
        "artifact_change_graph.json",
        "incremental_export_registry.json",
        "incremental_validation_registry.json",
        "export_cache_registry.json",
        "incremental_performance_comparison.json",
        "artifact_lifecycle_compaction_report.json",
        "topology_pruning_report.json",
        "superseded_artifact_registry.json",
        "stale_artifact_archive_registry.json",
        "topology_graph_registry.json",
        "topology_cycle_registry.json",
        "topology_cluster_registry.json",
        "review_path_optimization.json",
        "review_session_registry.json",
        "review_session_templates.json",
        "review_session_navigation.json",
        "export_lineage_registry.json",
        "corpus_evolution_registry.json",
        "historical_export_index.json",
        "longitudinal_review_registry.json",
        "lazy_generation_registry.json",
        "executive_synthesis_report.json",
        "critical_findings_registry.json",
        "review_priority_registry.json",
        "high_signal_artifact_registry.json",
        "dashboard_style_registry.json",
        "dashboard_consistency_validation.json",
        "dashboard_template_registry.json",
        "dashboard_aggregation_registry.json",
        "artifact_reduction_report.json",
        "review_workspace_registry.json",
        "review_checklists.json",
        "review_handoff_registry.json",
        "review_progress_templates.json",
        "change_intelligence_report.json",
        "longitudinal_summary_report.json",
        "trend_priority_registry.json",
        "evolution_highlights.json",
        "review_ux_registry.json",
        "information_density_registry.json",
        "dashboard_visibility_profiles.json",
        "pre_rc_readiness_report.json",
        "operational_risk_registry.json",
        "known_limitations_registry.json",
        "portable_metadata_compaction_report.json",
        "manual_review_requirements.json",
        "remaining_beta_blockers.json",
    }
    generated = []
    for path in sorted(package_root.rglob("*"), key=lambda item: item.relative_to(package_root).as_posix().lower()):
        if not path.is_file():
            continue
        rel = path.relative_to(package_root).as_posix()
        if rel in known:
            continue
        if rel in generated_roots or rel.startswith(("validation/", "manifests/", "assets/")):
            artifact_type = classify_file(package_root, path)
            display, analysis, validation = _artifact_flags(artifact_type, rel)
            generated.append(
                {
                    "source_path": None,
                    "package_path": rel,
                    "relative_path_from_index": rel,
                    "artifact_type": artifact_type,
                    "profile_inclusion": manifest.get("export_profile", "review"),
                    "inclusion_reason": "Generated by portable exporter.",
                    "human_review_value": _human_review_value(artifact_type, rel),
                    "linked_from_entrypoint": False,
                    "reachable_from_dashboard": False,
                    "required_for_offline_display": display or rel == "index.html",
                    "required_for_analysis_inspection": analysis,
                    "required_for_audit": artifact_type in {"manifest", "schema"} or rel.startswith("validation/"),
                    "required_for_validation": validation or rel.startswith("validation/"),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "dedupe_group_id": None,
                    "rewrite_status": "generated",
                    "validation_status": "pending",
                    "copied": False,
                    "generated": True,
                    "referenced_by": [],
                    "is_entrypoint": rel == "index.html",
                    "is_required_for_display": display or rel == "index.html",
                    "is_required_for_analysis": analysis,
                    "is_required_for_validation": validation or rel.startswith("validation/"),
                }
            )
    if generated:
        manifest["files"] = [*manifest.get("files", []), *generated]
        manifest["total_files"] = len(manifest["files"])
        manifest["total_bytes"] = sum(row.get("size_bytes", 0) for row in manifest["files"])


def _refresh_manifest_file_lists(package_root: Path, manifest: dict) -> None:
    files = [row for row in manifest.get("files", []) if row.get("package_path") and (package_root / row["package_path"]).exists()]
    manifest["files"] = files
    manifest["total_files"] = len(files)
    manifest["total_bytes"] = sum((package_root / row["package_path"]).stat().st_size for row in files)
    artifact_counts = Counter(row.get("artifact_type") for row in files)
    manifest["artifact_counts_by_type"] = dict(sorted(artifact_counts.items()))
    manifest["dashboards"] = [row["package_path"] for row in files if row.get("artifact_type") == "dashboard"]
    manifest["html_pages"] = [row["package_path"] for row in files if Path(row["package_path"]).suffix.lower() in {".html", ".htm"}]
    manifest["graphs"] = [row["package_path"] for row in files if row.get("artifact_type") == "graph"]
    manifest["images"] = [row["package_path"] for row in files if Path(row["package_path"]).suffix.lower() in IMAGE_EXTENSIONS]
    manifest["boards"] = [row["package_path"] for row in files if row.get("artifact_type") == "board" or any(t in row["package_path"].lower() for t in ("board", "storyboard", "contact_sheet", "giant"))]
    manifest["json_artifacts"] = [row["package_path"] for row in files if Path(row["package_path"]).suffix.lower() == ".json"]
    manifest["markdown_artifacts"] = [row["package_path"] for row in files if Path(row["package_path"]).suffix.lower() == ".md"]
    manifest["schemas"] = [row["package_path"] for row in files if row.get("artifact_type") == "schema"]
    manifest["manifests"] = [row["package_path"] for row in files if row.get("artifact_type") == "manifest"]
    manifest["validation_files"] = [row["package_path"] for row in files if "validation" in row["package_path"].lower()]
    manifest["interpretation_files"] = [row["package_path"] for row in files if "interpretation" in row["package_path"].lower()]
    manifest["recommendation_files"] = [row["package_path"] for row in files if "recommendation" in row["package_path"].lower()]
    manifest["evidence_files"] = [row["package_path"] for row in files if "evidence" in row["package_path"].lower()]
    manifest["governance_files"] = [row["package_path"] for row in files if "governance" in row["package_path"].lower()]
    manifest["review_files"] = [row["package_path"] for row in files if "review" in row["package_path"].lower()]
    manifest["timeline_files"] = [row["package_path"] for row in files if "timeline" in row["package_path"].lower()]
    manifest["snapshot_files"] = [row["package_path"] for row in files if "snapshot" in row["package_path"].lower()]
    manifest["diff_files"] = [row["package_path"] for row in files if "diff" in row["package_path"].lower() or "delta" in row["package_path"].lower()]
    manifest["replay_files"] = [row["package_path"] for row in files if "replay" in row["package_path"].lower()]


def _refresh_manifest_totals(package_root: Path, manifest: dict) -> None:
    """Refresh top-level inventory totals after late-generated export artifacts."""
    files = [path for path in package_root.rglob("*") if path.is_file()]
    manifest["total_files"] = len(files)
    manifest["total_bytes"] = sum(path.stat().st_size for path in files)


def _links_for(package_root: Path, predicate, limit: int = 250) -> str:
    items = []
    for path in sorted((item for item in package_root.rglob("*") if item.is_file() and predicate(item)), key=lambda item: item.relative_to(package_root).as_posix().lower())[:limit]:
        rel = path.relative_to(package_root).as_posix()
        if 'missing_asset_placeholder' in rel:
            continue
        items.append(f"<li><a href=\"{rel}\">{rel}</a></li>")
    return "<ul>" + "".join(items) + "</ul>" if items else "<p>None found.</p>"


def _governed_links(package_root: Path, governance: dict | None, category: str | None = None, limit: int = 24) -> str:
    if not governance:
        return "<p>Governance navigation is being generated.</p>"
    rows = governance.get("dashboard_governance_registry", {}).get("dashboards", [])
    selected = [
        row
        for row in rows
        if row.get("visibility") in {"primary", "visible", "advanced"}
        and is_analytical_review_target(row.get("package_path"))
        and not row.get("orphaned")
        and (category is None or row.get("category") == category)
    ]
    selected.sort(key=lambda row: (row.get("navigation_priority_score", 0), row.get("review_importance_score", 0)), reverse=True)
    items = []
    for row in selected[:limit]:
        rel = row.get("package_path")
        if rel and (package_root / rel).exists():
            items.append(
                f"<li><a href=\"{rel}\">{row.get('title') or rel}</a>"
                f"<span class=\"meta\">{row.get('category')} - priority {row.get('navigation_priority_score')}</span></li>"
            )
    return "<ul class=\"nav-list\">" + "".join(items) + "</ul>" if items else "<p>None found.</p>"


def _artifact_links(package_root: Path, manifest: dict, keys: list[str], limit: int = 12) -> str:
    paths: list[str] = []
    for key in keys:
        paths.extend(manifest.get(key) or [])
    seen = []
    for rel in paths:
        if rel not in seen and "missing_asset_placeholder" not in rel and (package_root / rel).exists():
            seen.append(rel)
    items = "".join(f"<li><a href=\"{rel}\">{rel}</a></li>" for rel in seen[:limit])
    return "<ul class=\"nav-list\">" + items + "</ul>" if items else "<p>None found.</p>"


def _size_mb(manifest: dict) -> str:
    return f"{round((manifest.get('total_bytes') or 0) / (1024 * 1024), 2)} MB"


def write_master_index(
    package_root: Path,
    manifest: dict,
    validation: dict,
    governance: dict | None = None,
    review_sessions: dict | None = None,
    synthesis: dict | None = None,
    reduction: dict | None = None,
    change_intelligence: dict | None = None,
    pre_rc: dict | None = None,
) -> None:
    summary = validation.get("summary", {})
    dashboard_link = "visualizations/dashboard.html" if (package_root / "visualizations" / "dashboard.html").exists() else None
    corpus_dashboard_link = "visualizations/corpus_dashboard.html" if (package_root / "visualizations" / "corpus_dashboard.html").exists() else dashboard_link
    dashboard_html = f"<p><a href=\"{corpus_dashboard_link}\">Open main dashboard</a></p>" if corpus_dashboard_link else "<p>Main dashboard not found.</p>"
    topology_page = (governance or {}).get("topology_page")
    topology_html = f"<p><a href=\"{topology_page}\">Open compressed review topology</a></p>" if topology_page else ""
    governance_links = (
        '<a href="dashboard_governance_registry.json">Dashboard governance</a> | '
        '<a href="artifact_importance_registry.json">Importance registry</a> | '
        '<a href="review_pathways.json">Review pathways</a>'
        if governance
        else "Dashboard governance is being generated."
    )
    coherence = (governance or {}).get("review_coherence_report", {})
    consolidation = (governance or {}).get("dashboard_consolidation_report", {})
    orphan_summary = ((governance or {}).get("artifact_orphan_registry") or {}).get("summary", {})
    dedupe_summary = manifest.get("dedupe_summary", {})
    pathway_rows = ((governance or {}).get("review_pathways") or {}).get("pathways", [])
    pathway_html = "".join(
        "<details><summary>{}</summary><ol>{}</ol></details>".format(
            pathway.get("pathway_intent", pathway.get("pathway_id")).title(),
            "".join(f"<li><a href=\"{path}\">{path}</a></li>" for path in [item for item in (pathway.get("recommended_navigation_order") or []) if item != 'index.html'][:8]),
        )
        for pathway in pathway_rows
    ) or "<p>Review pathways are being generated.</p>"
    session_html = render_review_session_index(review_sessions or {}) if review_sessions else "<p>Guided review sessions are being generated.</p>"
    session_nav = (review_sessions or {}).get("review_session_navigation", {})
    resume_review = session_nav.get("resume_review") or "Open main dashboard"
    next_dashboard = session_nav.get("recommended_next_dashboard") or corpus_dashboard_link or "index.html"
    synthesis_report = (synthesis or {}).get("executive_synthesis_report", {})
    top_findings = synthesis_report.get("top_findings") or []
    top_finding_html = "<ol>" + "".join(
        f"<li><strong>{finding.get('title')}</strong><br><span class=\"meta\">{finding.get('severity')} - priority {finding.get('review_priority')}</span><p>{finding.get('summary')}</p></li>"
        for finding in top_findings[:5]
    ) + "</ol>" if top_findings else "<p>Top findings are being generated.</p>"
    priority_html = "<ol>" + "".join(
        f"<li><a href=\"{row.get('review_target') or 'portable_package_validation_report.json'}\">{row.get('recommended_action')}</a><br><span class=\"meta\">priority {row.get('priority_score')}</span></li>"
        for row in synthesis_report.get("highest_priority_review_actions", [])[:6]
    ) + "</ol>" if synthesis_report.get("highest_priority_review_actions") else "<p>Priority actions are being generated.</p>"
    change_html = "<ul>" + "".join(f"<li>{item}</li>" for item in (change_intelligence or {}).get("what_matters_most", [])[:5]) + "</ul>" if change_intelligence else "<p>Change highlights are being generated.</p>"
    limitations = ((pre_rc or {}).get("known_limitations_registry") or {}).get("limitations", [])
    limitations_html = "<ul>" + "".join(f"<li>{row.get('summary')}</li>" for row in limitations[:5]) + "</ul>" if limitations else "<p>Known beta limitations are being generated.</p>"
    reduction_summary = (reduction or {}).get("summary", {})
    demo_html = '<section><h2>Five-minute video walkthrough</h2><p><a href="demo_walkthrough.html">Finding → evidence → recommendation → saved notes</a></p><p>Static notes require an explicit download. Original media is not bundled.</p></section>' if (package_root / 'demo_walkthrough.html').is_file() else ''
    fallback_html = '<p class="warning">Broken-link validation checks whether links resolve, including placeholders. Unavailable source evidence is disclosed separately in the <a href="validation/portable_fallback_link_audit.json">fallback-link audit</a>.</p>' if (package_root / 'validation/portable_fallback_link_audit.json').is_file() else ''
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Portable Review Package</title><style>
body{{font-family:Arial,sans-serif;margin:0;line-height:1.45;color:#222;background:#f7f7f5}}a{{color:#245f86}}
header{{padding:28px 32px;background:#fff;border-bottom:1px solid #ddd}}main{{padding:0 32px 32px;max-width:1180px}}
section{{margin:24px 0}}.status{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}}
.metric{{border:1px solid #ccc;background:#fff;padding:12px;border-radius:6px}}.warning{{border-left:5px solid #9c4f45;background:#fff;padding:12px}}
.nav-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}}.panel{{border:1px solid #d8d8d8;background:#fff;padding:14px;border-radius:6px}}
.nav-list{{list-style:none;padding:0;margin:0}}.nav-list li{{margin:9px 0;display:flex;flex-direction:column}}.meta{{color:#666;font-size:12px}}
details{{border:1px solid #ddd;background:#fff;margin:10px 0;padding:10px;border-radius:6px}}summary{{cursor:pointer;font-weight:700}}
.search{{width:100%;max-width:520px;padding:10px;border:1px solid #aaa;border-radius:6px}}
</style></head><body>
<header><h1>Portable Review Package</h1>
<p>Generated at UTC: {manifest.get("generation_timestamp")}</p>
<p>Profile: <strong>{manifest.get("export_profile", "review")}</strong></p>
<div class="warning"><strong>Raw Media Exclusion Notice:</strong> raw source video files are excluded by default. This package preserves analytical outputs, dashboards, visualizations, reports, review artifacts, evidence, interpretations, and validation files needed for offline review.</div></header>
<main>
{demo_html}
{fallback_html}
<div class="status">
<div class="metric"><strong>Validation</strong><br>{validation.get("validation_passed")}</div>
<div class="metric"><strong>Broken links</strong><br>{summary.get("broken_link_count")}</div>
<div class="metric"><strong>Missing assets</strong><br>{summary.get("missing_asset_count")}</div>
<div class="metric"><strong>Dashboards</strong><br>{summary.get("dashboard_count")}</div>
<div class="metric"><strong>Profile</strong><br>{manifest.get("export_profile", "review")}</div>
<div class="metric"><strong>Package size</strong><br>{_size_mb(manifest)}</div>
<div class="metric"><strong>Images</strong><br>{summary.get("image_count")}</div>
<div class="metric"><strong>Compressed pages</strong><br>{consolidation.get("pages_before", "?")} to {consolidation.get("pages_after", "?")}</div>
<div class="metric"><strong>Orphans</strong><br>{orphan_summary.get("orphan_count", "?")}</div>
<div class="metric"><strong>Dedupe saved</strong><br>{dedupe_summary.get("dedupe_savings_bytes", 0)} bytes</div>
<div class="metric"><strong>Review hours</strong><br>{coherence.get("estimated_human_review_hours", "?")}</div>
<div class="metric"><strong>Cognitive reduction</strong><br>{reduction_summary.get("estimated_cognitive_reduction", "?")}</div>
</div>
<section><h2>Executive Summary</h2><p>{synthesis_report.get("concise_summary", "Open the recommended review path and inspect top findings first.")}</p><p><a href="executive_synthesis_report.json">Executive synthesis report</a></p></section>
<section><h2>Top Findings</h2>{top_finding_html}</section>
<section><h2>Highest Priority Review Actions</h2>{priority_html}</section>
<section><h2>Recommended Review Pathway</h2><p class="meta">Review Pathways</p>{pathway_html}</section>
<section><h2>Most Important Dashboards</h2>{_governed_links(package_root, governance, None, 8)}</section>
<section><h2>Change Highlights</h2>{change_html}</section>
<section><h2>Open This First</h2><p class="meta">Start Here</p>{dashboard_html}{topology_html}</section>
<section><h2>Resume Review</h2><p class="meta">Resume: {resume_review}</p><p><a href="{next_dashboard}">Recommended next dashboard</a></p></section>
<section><h2>Review Workspace Links</h2><p><a href="review/review_workspace_registry.json">Workspace registry</a> | <a href="review/review_checklists.json">Review checklists</a> | <a href="review/review_handoff_registry.json">Handoff registry</a></p></section>
<section><h2>Send This File</h2><p>{Path(manifest.get('zip_path') or '').name if manifest.get('zip_path') else 'Zip not generated - send the package folder.'}</p></section>
<section><h2>What To Do Next</h2><ol><li>Open the main dashboard.</li><li>Follow the recommended review path.</li><li>Check Package Validation before sending the zip.</li></ol></section>
<p><a href="PACKAGE_SUMMARY.md">Package summary</a> | <a href="portable_package_manifest.json">Package manifest</a> | <a href="portable_package_validation_report.json">Validation report</a> | {governance_links}</p>
<section class="panel"><h2>Search / Filter</h2><input class="search" id="filter" placeholder="Filter visible navigation"><script>document.getElementById('filter').addEventListener('input',e=>{{const q=e.target.value.toLowerCase();document.querySelectorAll('li').forEach(n=>{{n.style.display=n.textContent.toLowerCase().includes(q)?'':'none'}})}})</script></section>
<section><h2>Executive Summary Source Reports</h2>{_artifact_links(package_root, manifest, ["markdown_artifacts"], 8)}</section>
<section><h2>Guided Review Sessions</h2>{session_html}</section>
<section><h2>Top Dashboards</h2>{_governed_links(package_root, governance, None, 12)}</section>
<section><h2>Key Graphs</h2>{_artifact_links(package_root, manifest, ["graphs", "images"], 12)}</section>
<section><h2>Top Recommendations</h2>{_governed_links(package_root, governance, "recommendation", 10)}</section>
<section><h2>Governance Concerns</h2>{_governed_links(package_root, governance, "governance", 10)}</section>
<section><h2>Governance / Readiness</h2>{_governed_links(package_root, governance, "governance", 10)}</section>
<section><h2>Recommendation Highlights</h2>{_governed_links(package_root, governance, "recommendation", 10)}</section>
<section><h2>Evidence and Timelines</h2><div class="nav-grid"><div class="panel"><h3>Evidence</h3>{_governed_links(package_root, governance, "evidence")}</div><div class="panel"><h3>Timelines</h3>{_governed_links(package_root, governance, "continuity")}{_artifact_links(package_root, manifest, ["timeline_files"], 8)}</div></div></section>
<section><h2>Interpretation Pages</h2>{_governed_links(package_root, governance, "interpretation", 16)}</section>
<section><h2>Validation Summary</h2><ul><li><a href="portable_package_validation_report.json">Validation report</a></li><li><a href="dashboard_consistency_validation.json">Dashboard consistency validation</a></li><li><a href="dashboard_governance_validation.json">Dashboard governance validation</a></li><li><a href="review_pathway_validation.json">Review pathway validation</a></li><li><a href="asset_rewrite_validation.json">Asset rewrite validation</a></li></ul></section>
<section><h2>Package Validation</h2><ul><li><a href="portable_package_validation_report.json">Validation report</a></li><li><a href="dashboard_governance_validation.json">Dashboard governance validation</a></li><li><a href="review_pathway_validation.json">Review pathway validation</a></li><li><a href="asset_rewrite_validation.json">Asset rewrite validation</a></li><li><a href="portable_export_performance_report.json">Performance report</a></li></ul></section>
<section><h2>Known Limitations</h2>{limitations_html}</section>
<section><h2>Beta Warning</h2><p>Classification remains <strong>operational beta+ / internal beta_plus</strong>. RC promotion is not recommended yet.</p></section>
<details><summary>Advanced Audit Material</summary><p class="meta">Audit Details</p><p class="meta">Advanced / Audit-Only Dashboards</p>{_governed_links(package_root, governance, "audit", 80)}<p><a href="pre_rc_readiness_report.json">Pre-RC readiness report</a> | <a href="remaining_beta_blockers.json">Remaining beta blockers</a></p></details>
<section><h2>Raw Media Exclusion Notice</h2><p>Raw media included: <strong>{manifest.get("raw_media_included")}</strong>. Raw media excluded count: <strong>{manifest.get("raw_media_excluded_count")}</strong>.</p></section>
<details><summary>Raw Inventories</summary>
<section><h2>Graphs and Image Inventory</h2>{_links_for(package_root, lambda p: p.suffix.lower() in IMAGE_EXTENSIONS)}</section>
<section><h2>Markdown Reports</h2>{_links_for(package_root, lambda p: p.suffix.lower() == ".md")}</section>
<section><h2>JSON Artifacts, Manifests, Schemas, Validation</h2>{_links_for(package_root, lambda p: p.suffix.lower() == ".json")}</section>
</details>
</main></body></html>"""
    (package_root / "index.html").write_text(html, encoding="utf-8")


def write_package_summary(
    package_root: Path,
    manifest: dict,
    validation: dict,
    size_report: dict,
    exclusion_manifest: dict,
    privacy_report: dict,
    zip_path: Path | None,
    reachability: dict | None = None,
) -> None:
    summary = validation.get("summary", {})
    size_summary = size_report.get("summary", {})
    lines = [
        "# Package Summary",
        "",
        "## Purpose",
        "This portable package is a standalone analytical deliverable for offline review of generated video-insight-bundler corpus outputs.",
        "",
        "## Generation",
        f"- Generated at UTC: {manifest.get('generation_timestamp')}",
        f"- Source analysis root: {manifest.get('source_analysis_root')}",
        f"- Analyzed video/corpus: {manifest.get('requested_video') or manifest.get('source_analysis_root')}",
        f"- Export profile: {manifest.get('export_profile')}",
        f"- Package root: {manifest.get('package_root')}",
        f"- Zip path: {zip_path.resolve().as_posix() if zip_path else 'not generated'}",
        f"- Raw media included: {manifest.get('raw_media_included')}",
        f"- Raw media excluded count: {manifest.get('raw_media_excluded_count')}",
        "",
        "## Open This First",
        f"`{(Path(manifest.get('package_root') or package_root) / 'index.html').resolve().as_posix()}`",
        "",
        "## Send This File",
        f"`{zip_path.resolve().as_posix() if zip_path else 'Zip was not generated for this run.'}`",
        "",
        "## Inventory",
        f"- Dashboards preserved: {summary.get('dashboard_count')}",
        f"- HTML pages preserved: {summary.get('html_page_count')}",
        f"- Graphs preserved: {summary.get('graph_count')}",
        f"- PNG/images preserved: {summary.get('image_count')}",
        f"- Giant boards/contact sheets: {summary.get('giant_board_count')}",
        f"- JSON files preserved: {summary.get('json_count')}",
        f"- Markdown/report files preserved: {summary.get('markdown_count')}",
        f"- Manifests preserved: {summary.get('manifest_count')}",
        f"- Schemas preserved: {summary.get('schema_count')}",
        f"- Interpretation artifacts preserved: {summary.get('interpretation_artifact_count')}",
        f"- Validation artifacts preserved: {summary.get('validation_artifact_count')}",
        "",
        "## Validation",
        f"- Offline readiness status: {validation.get('validation_passed')}",
        f"- Broken links count: {validation.get('broken_link_count')}",
        f"- Missing assets count: {validation.get('missing_asset_count')}",
        f"- Absolute live path dependency count: {validation.get('absolute_live_path_count')}",
        f"- Remote dependency count: {validation.get('remote_dependency_count')}",
        f"- Privacy/risky file count: {privacy_report.get('summary', {}).get('risky_file_count')}",
        f"- Recursive package inclusion detected: {validation.get('recursive_package_inclusion_detected', False)}",
        f"- Source video placeholders inserted: {summary.get('source_video_placeholder_count')}",
        f"- Enriched page section hits: {summary.get('enriched_page_section_hit_count')}",
        "",
        "## Size",
        f"- Total package size bytes: {size_summary.get('total_package_size_bytes')}",
        f"- Zip size bytes: {size_summary.get('zip_size_bytes')}",
        f"- Size saved by excluding raw media bytes: {size_summary.get('size_saved_by_excluding_raw_media_bytes')}",
        "",
        "## Exclusions",
        f"- Total excluded files: {exclusion_manifest.get('summary', {}).get('excluded_file_count')}",
        f"- Raw media excluded files: {exclusion_manifest.get('summary', {}).get('raw_media_excluded_count')}",
        "Raw videos and source media are excluded by default so the package can be shared as an analytical review deliverable without redistributing original media.",
        "",
        "## Profile Notes",
        f"This package used the `{manifest.get('export_profile')}` profile. Use `--export-profile full` for the broadest non-video package, or `--export-profile audit` for more provenance/schemas/validation artifacts.",
        "",
        "## Reachability",
        f"- Reachable files: {(reachability or {}).get('summary', {}).get('reachable_file_count')}",
        f"- Unreachable suspicious files: {(reachability or {}).get('summary', {}).get('unreachable_suspicious_count')}",
        "",
        "## Dashboard Governance",
        f"- Dashboard governance registry: `dashboard_governance_registry.json`",
        f"- Artifact importance registry: `artifact_importance_registry.json`",
        f"- Review pathways: `review_pathways.json`",
        f"- Orphan registry: `artifact_orphan_registry.json`",
        f"- Review coherence report: `review_coherence_report.json`",
        "Navigation is hierarchical by default; advanced and audit-only artifacts are collapsed in `index.html`.",
        "",
        "## Recipient Instructions",
        "1. Unzip the package.",
        "2. Open `index.html` directly in a browser.",
        "3. Browse dashboards and reports from the master index.",
        "4. Inspect JSON and Markdown artifacts if needed.",
        "",
        "## Warnings",
    ]
    warnings = validation.get("warnings", [])[:50] or ["None detected by portable validation."]
    lines.extend(f"- {warning}" for warning in warnings)
    (package_root / "PACKAGE_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def zip_package(package_root: Path, compression_level: int = 8, zip_mode: str = "full") -> Path:
    zip_path, _report = build_zip_file(package_root, compression_level=compression_level, zip_mode=zip_mode)
    return zip_path


def _zip_snapshot(package_root: Path, zip_path: Path, compression_level: int) -> None:
    """Archive the verified tree without mutating its ZIP assembly evidence."""
    compression = zipfile.ZIP_STORED if compression_level == 0 else zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(zip_path, "w", compression=compression, compresslevel=compression_level if compression_level else None) as archive:
        for path in sorted(package_root.rglob("*")):
            if path.is_file():
                archive.write(path, package_root.name + "/" + path.relative_to(package_root).as_posix())


def _reconcile_package_inventory(package_root: Path, manifest: dict, *, source_root: Path, zip_path: Path | None, exclusions: list[dict], max_file_size_warning_mb: float) -> dict:
    """Reconcile totals after metadata writes, including the reports themselves."""
    for _ in range(8):
        _refresh_manifest_totals(package_root, manifest)
        write_json(package_root / "portable_package_manifest.json", manifest)
        index_path = package_root / "index.html"
        if index_path.exists():
            index = index_path.read_text(encoding="utf-8")
            index = re.sub(r"(<strong>Package size</strong><br>)[^<]+", lambda match: match.group(1) + _size_mb(manifest), index)
            index_path.write_text(index, encoding="utf-8")
        summary_path = package_root / "PACKAGE_SUMMARY.md"
        if summary_path.exists():
            summary = summary_path.read_text(encoding="utf-8")
            summary = re.sub(r"(?m)^- Total package size bytes: .*", f"- Total package size bytes: {manifest['total_bytes']}", summary)
            summary_path.write_text(summary, encoding="utf-8")
        size_report = write_size_report(package_root, source_root=source_root, zip_path=zip_path, exclusions=exclusions, max_file_size_warning_mb=max_file_size_warning_mb)
        actual = sum(path.stat().st_size for path in package_root.rglob("*") if path.is_file())
        if manifest["total_bytes"] == actual == size_report["summary"]["total_package_size_bytes"]:
            return size_report
    raise RuntimeError("Package inventory totals did not stabilize after final metadata writes.")


def _preferred_canonical_duplicate(files: list[dict]) -> str:
    def key(row: dict) -> tuple[int, int, str]:
        path = str(row.get("path") or "")
        lower = path.lower()
        if lower.startswith("graphs/"):
            rank = 0
        elif lower.startswith("visualizations/"):
            rank = 1
        elif lower.startswith("assets/images/"):
            rank = 2
        else:
            rank = 3
        return rank, len(path), path

    return sorted(files, key=key)[0].get("path")


def _portable_rel_link(from_file: Path, to_file: Path, package_root: Path) -> str:
    try:
        return Path(os.path.relpath(to_file.resolve(), from_file.parent.resolve())).as_posix()
    except ValueError:
        return to_file.resolve().relative_to(package_root.resolve()).as_posix()


def _rewrite_duplicate_references(package_root: Path, duplicate_rel: str, canonical_rel: str) -> int:
    duplicate = package_root / duplicate_rel
    canonical = package_root / canonical_rel
    changed = 0
    for path in sorted(package_root.rglob("*"), key=lambda item: item.relative_to(package_root).as_posix().lower()):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        original = text
        candidates = {
            duplicate_rel,
            duplicate_rel.replace("/", "\\"),
            _portable_rel_link(path, duplicate, package_root),
            _portable_rel_link(path, duplicate, package_root).replace("/", "\\"),
        }
        replacement = _portable_rel_link(path, canonical, package_root)
        for candidate in sorted(candidates, key=len, reverse=True):
            if candidate:
                text = text.replace(candidate, replacement)
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed += 1
    return changed


def _has_text_reference(package_root: Path, rel: str) -> bool:
    target = package_root / rel
    for path in sorted(package_root.rglob("*"), key=lambda item: item.relative_to(package_root).as_posix().lower()):
        if not path.is_file() or path == target or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        candidates = {
            rel,
            rel.replace("/", "\\"),
            _portable_rel_link(path, target, package_root),
            _portable_rel_link(path, target, package_root).replace("/", "\\"),
        }
        if any(candidate and candidate in text for candidate in candidates):
            return True
    return False


def _write_dedupe_report(package_root: Path, mode: str = "report") -> dict:
    before_groups: dict[str, list[dict]] = {}
    for path in sorted(package_root.rglob("*"), key=lambda item: item.relative_to(package_root).as_posix().lower()):
        if path.is_file() and path.suffix.lower() in DEDUPE_DISPLAY_EXTENSIONS:
            digest = sha256_file(path)
            before_groups.setdefault(digest, []).append({"path": path.relative_to(package_root).as_posix(), "size_bytes": path.stat().st_size})
    duplicate_groups_before = [
        {"dedupe_group_id": f"dup_{index:04d}", "sha256": digest, "files": rows, "duplicate_bytes": (len(rows) - 1) * rows[0]["size_bytes"]}
        for index, (digest, rows) in enumerate(before_groups.items(), 1)
        if len(rows) > 1
    ]
    groups: dict[str, list[dict]] = {}
    for path in sorted(package_root.rglob("*"), key=lambda item: item.relative_to(package_root).as_posix().lower()):
        if path.is_file():
            digest = sha256_file(path)
            groups.setdefault(digest, []).append({"path": path.relative_to(package_root).as_posix(), "size_bytes": path.stat().st_size})
    duplicate_groups = [
        {"dedupe_group_id": f"dup_{index:04d}", "sha256": digest, "files": rows, "duplicate_bytes": (len(rows) - 1) * rows[0]["size_bytes"]}
        for index, (digest, rows) in enumerate(groups.items(), 1)
        if len(rows) > 1
    ]
    deduped_groups = []
    dedupe_savings = 0
    skipped_groups = []
    # A package continues to gain dashboards after this report is written.
    # Retaining duplicate display assets in safe mode prevents later-generated
    # pages from acquiring references to a deleted asset. Deletion remains an
    # explicit experimental opt-in until the full generation pipeline can
    # prove all later references are canonicalized.
    if mode == "aggressive-experimental":
        for group in duplicate_groups:
            files = group.get("files") or []
            canonical = _preferred_canonical_duplicate(files)
            removed = []
            rewritten_reference_count = 0
            for row in files:
                duplicate_rel = row.get("path")
                if not duplicate_rel or duplicate_rel == canonical:
                    continue
                if Path(duplicate_rel).suffix.lower() not in DEDUPE_DISPLAY_EXTENSIONS:
                    skipped_groups.append({"dedupe_group_id": group.get("dedupe_group_id"), "path": duplicate_rel, "reason": "not_safe_display_asset"})
                    continue
                rewritten_reference_count += _rewrite_duplicate_references(package_root, duplicate_rel, canonical)
                duplicate_path = package_root / duplicate_rel
                if duplicate_path.exists() and not _has_text_reference(package_root, duplicate_rel):
                    size = duplicate_path.stat().st_size
                    duplicate_path.unlink()
                    removed.append({"path": duplicate_rel, "size_bytes": size})
                    dedupe_savings += size
            if removed:
                deduped_groups.append(
                    {
                        "dedupe_group_id": group.get("dedupe_group_id"),
                        "canonical_path": canonical,
                        "removed_duplicates": removed,
                        "rewritten_reference_count": rewritten_reference_count,
                    }
                )
            elif files:
                skipped_groups.append({"dedupe_group_id": group.get("dedupe_group_id"), "canonical_path": canonical, "reason": "references_not_safely_rewritten_or_no_safe_duplicate"})
    after_groups: dict[str, list[dict]] = {}
    for path in sorted(package_root.rglob("*"), key=lambda item: item.relative_to(package_root).as_posix().lower()):
        if path.is_file() and path.suffix.lower() in DEDUPE_DISPLAY_EXTENSIONS:
            digest = sha256_file(path)
            after_groups.setdefault(digest, []).append({"path": path.relative_to(package_root).as_posix(), "size_bytes": path.stat().st_size})
    duplicate_groups_after = [
        {"sha256": digest, "files": rows, "duplicate_bytes": (len(rows) - 1) * rows[0]["size_bytes"]}
        for digest, rows in after_groups.items()
        if len(rows) > 1
    ]
    report = {
        "analysis_status": "complete",
        "method": "portable_deduplication_v2",
        "generated_at_utc": utc_now_iso(),
        "mode": mode,
        "duplicate_groups": duplicate_groups,
        "duplicate_groups_before": duplicate_groups_before,
        "duplicate_groups_after": duplicate_groups_after,
        "total_duplicate_bytes": sum(row["duplicate_bytes"] for row in duplicate_groups),
        "safe_to_dedupe_groups": [] if mode not in {"safe", "aggressive-experimental"} else duplicate_groups_before,
        "deduped_groups": deduped_groups,
        "dedupe_savings_bytes": dedupe_savings,
        "links_rewritten": sum(row.get("rewritten_reference_count", 0) for row in deduped_groups),
        "links_validated": 0,
        "skipped_groups": skipped_groups,
        "skipped_reason": (
            "Conservative default reports duplicates only; links are not rewritten."
            if mode == "report"
            else "Safe mode reports duplicates without deleting assets; use aggressive-experimental only when asset removal is explicitly accepted."
            if mode == "safe"
            else None
        ),
        "summary": {
            "duplicate_group_count": len(duplicate_groups_before),
            "duplicate_group_count_before": len(duplicate_groups_before),
            "duplicate_group_count_after": len(duplicate_groups_after),
            "potential_dedupe_savings_bytes": sum(row["duplicate_bytes"] for row in duplicate_groups_before),
            "deduped_group_count": len(deduped_groups),
            "dedupe_savings_bytes": dedupe_savings,
            "bytes_saved": dedupe_savings,
            "links_rewritten": sum(row.get("rewritten_reference_count", 0) for row in deduped_groups),
            "skipped_group_count": len(skipped_groups),
        },
    }
    write_json(package_root / "portable_deduplication_report.json", report)
    write_json(package_root / "validation" / "portable_deduplication_report.json", report)
    return report


def _write_canonical_asset_registry(package_root: Path, dedupe_report: dict) -> dict:
    groups: dict[str, list[dict]] = {}
    for path in sorted(package_root.rglob("*"), key=lambda item: item.relative_to(package_root).as_posix().lower()):
        if path.is_file() and path.suffix.lower() in DEDUPE_DISPLAY_EXTENSIONS:
            groups.setdefault(sha256_file(path), []).append({"path": path.relative_to(package_root).as_posix(), "size_bytes": path.stat().st_size})
    assets = []
    for digest, rows in sorted(groups.items()):
        canonical = _preferred_canonical_duplicate(rows)
        assets.append(
            {
                "asset_hash": digest,
                "canonical_path": canonical,
                "duplicate_paths": [row["path"] for row in rows if row["path"] != canonical],
                "display_asset_type": Path(canonical).suffix.lower().lstrip("."),
                "safe_dedupe_candidate": len(rows) > 1 and Path(canonical).suffix.lower() in DEDUPE_DISPLAY_EXTENSIONS,
                "files": rows,
            }
        )
    report = {
        "analysis_status": "complete",
        "method": "canonical_display_asset_registry_v2",
        "generated_at_utc": utc_now_iso(),
        "dedupe_mode": dedupe_report.get("mode"),
        "assets": assets,
        "summary": {
            "asset_group_count": len(assets),
            "duplicate_asset_group_count": sum(1 for row in assets if row["duplicate_paths"]),
            "duplicate_asset_count": sum(len(row["duplicate_paths"]) for row in assets),
            "bytes_saved": dedupe_report.get("dedupe_savings_bytes", 0),
        },
    }
    write_json(package_root / "canonical_asset_registry.json", report)
    write_json(package_root / "governance" / "canonical_asset_registry.json", report)
    return report


def _write_asset_rewrite_validation(package_root: Path, dedupe_report: dict) -> dict:
    validation = validate_portable_package(package_root, strict=False)
    removed = [row["path"] for group in dedupe_report.get("deduped_groups", []) for row in group.get("removed_duplicates", [])]
    lingering = [rel for rel in removed if _has_text_reference(package_root, rel)]
    report = {
        "analysis_status": "complete" if not lingering and validation.get("validation_passed") else "error",
        "method": "asset_rewrite_validation_v1",
        "generated_at_utc": utc_now_iso(),
        "removed_duplicate_paths": removed,
        "lingering_removed_asset_references": lingering,
        "links_rewritten": dedupe_report.get("summary", {}).get("links_rewritten", 0),
        "links_validated": validation.get("summary", {}).get("html_page_count", 0) + validation.get("css_files_checked", 0) + validation.get("js_files_checked", 0),
        "validation_passed": not lingering and validation.get("validation_passed"),
        "broken_link_count": validation.get("broken_link_count"),
        "missing_asset_count": validation.get("missing_asset_count"),
    }
    dedupe_report["links_validated"] = report["links_validated"]
    dedupe_report.setdefault("summary", {})["links_validated"] = report["links_validated"]
    write_json(package_root / "asset_rewrite_validation.json", report)
    write_json(package_root / "validation" / "asset_rewrite_validation.json", report)
    write_json(package_root / "portable_deduplication_report.json", dedupe_report)
    write_json(package_root / "validation" / "portable_deduplication_report.json", dedupe_report)
    return report


def _validate_extracted_zip(zip_path: Path, *, strict: bool, allow_provenance_absolute_paths: bool, raw_media_allowed: bool, export_profile: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="portable_extract_") as temp:
        root = Path(temp)
        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(root)
        package_root = root / zip_path.with_suffix("").name
        return validate_portable_package(
            package_root,
            strict=strict,
            allow_provenance_absolute_paths=allow_provenance_absolute_paths,
            raw_media_allowed=raw_media_allowed,
            export_profile=export_profile,
            zip_created=True,
            zip_validated=True,
            extracted_zip_validated=True,
        )


def _write_asset_dependency_report(package_root: Path) -> dict:
    report = scan_asset_dependencies(package_root, package_root=package_root, scan_references=False)
    write_json(package_root / "manifests" / "asset_dependency_report.json", report)
    return report


def _write_verification_summary(source_root: Path, package_root: Path, validation: dict, manifest: dict, zip_path: Path | None) -> None:
    evidence_dir = source_root / "verification_evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        evidence_dir / "portable_export_validation.json",
        {
            "analysis_status": "complete" if validation.get("validation_passed") else "error",
            "method": "portable_export_validation_summary_v1",
            "generated_at_utc": utc_now_iso(),
            "package_root": package_root.resolve().as_posix(),
            "zip_path": zip_path.resolve().as_posix() if zip_path else None,
            "validation_summary": validation.get("summary", {}),
            "manifest_summary": {
                "total_files": manifest.get("total_files"),
                "total_bytes": manifest.get("total_bytes"),
                "raw_media_included": manifest.get("raw_media_included"),
                "raw_media_excluded_count": manifest.get("raw_media_excluded_count"),
            },
        },
    )


def _write_profile_comparison_report(package_root: Path, source_root: Path, active_profile: str, include_raw_media: bool) -> dict:
    rows = []
    for profile in sorted(EXPORT_PROFILES):
        if profile == active_profile:
            root = package_root
            files = [
                {"path": path.relative_to(root).as_posix(), "extension": path.suffix.lower(), "category": classify_file(root, path), "size_bytes": path.stat().st_size}
                for path in root.rglob("*")
                if path.is_file()
            ]
        else:
            files = []
            for path in source_root.rglob("*"):
                if not path.is_file():
                    continue
                exclude, _reason, _rule = should_exclude_path(path, source_root, include_raw_media=include_raw_media, export_profile=profile)
                if not exclude:
                    rel = path.relative_to(source_root).as_posix()
                    files.append({"path": rel, "extension": path.suffix.lower(), "category": classify_file(source_root, path), "size_bytes": path.stat().st_size})
        rows.append(
            {
                "profile": profile,
                "active_export": profile == active_profile,
                "file_count": len(files),
                "size_bytes": sum(row["size_bytes"] for row in files),
                "dashboard_count": sum(1 for row in files if row["category"] == "dashboard"),
                "json_count": sum(1 for row in files if row["extension"] == ".json"),
                "validation_count": sum(1 for row in files if "validation" in row["path"].lower()),
                "intended_use_case": PROFILE_USE_CASES[profile],
                "intentionally_excluded": PROFILE_EXCLUSIONS[profile],
                "recommended_profile": profile == "review",
            }
        )
    report = {
        "analysis_status": "complete",
        "method": "portable_profile_comparison_v1",
        "generated_at_utc": utc_now_iso(),
        "recommended_profile": "review",
        "active_profile": active_profile,
        "profiles": rows,
    }
    write_json(package_root / "portable_profile_comparison_report.json", report)
    lines = ["# Portable Profile Comparison", "", "Recommended profile: `review`", ""]
    lines.append("| Profile | Active | Files | Bytes | Dashboards | JSON | Validation | Use case | Excluded |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |")
    for row in rows:
        lines.append(
            f"| {row['profile']} | {row['active_export']} | {row['file_count']} | "
            f"{row['size_bytes']} | {row['dashboard_count']} | "
            f"{row['json_count']} | {row['validation_count']} | "
            f"{row['intended_use_case']} | {row['intentionally_excluded']} |"
        )
    (package_root / "portable_profile_comparison_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def _write_performance_report(package_root: Path, timings: dict) -> dict:
    report = {
        "analysis_status": "complete",
        "method": "portable_export_performance_v1",
        "generated_at_utc": utc_now_iso(),
        "timings": timings,
        "breakdown": {
            "scan": timings.get("scan_duration_seconds"),
            "copy": timings.get("copy_duration_seconds"),
            "rewrite": timings.get("rewrite_duration_seconds"),
            "dedupe": timings.get("dedupe_duration_seconds"),
            "governance_generation": timings.get("governance_generation_duration_seconds"),
            "index_generation": timings.get("index_generation_duration_seconds"),
            "zip": timings.get("zip_duration_seconds"),
            "validation": timings.get("validation_duration_seconds"),
            "extracted_validation": timings.get("extracted_validation_duration_seconds"),
        },
        "optimizations": [
            "Reference scanning is reused for manifest construction during one export run.",
            "Binary assets are checksum grouped once for dedupe and canonical registry generation.",
            "Extracted zip validation is optional because it is the slowest validation path on large packages.",
        ],
        "slowest_steps": sorted(
            [{"step": key, "duration_seconds": value} for key, value in timings.items() if isinstance(value, (int, float))],
            key=lambda row: row["duration_seconds"],
            reverse=True,
        )[:9],
    }
    write_json(package_root / "portable_export_performance_report.json", report)
    write_json(package_root / "validation" / "portable_export_performance_report.json", report)
    return report


def build_portable_package(
    output_dir: Path,
    dest_root: Path | None = None,
    *,
    zip_export: bool = False,
    include_raw_media: bool = False,
    strict: bool = True,
    allow_provenance_absolute_paths: bool = True,
    max_file_size_warning_mb: float = 100.0,
    copy_mode: str = "copy",
    export_profile: str = "review",
    dedupe: str = "report",
    dashboard_consolidation: str = "grouped",
    compression_level: int = 8,
    validate_extracted: bool = False,
    validation_tier: str = "standard",
    generation_mode: str = "hybrid",
    cache_mode: str = "auto",
    zip_mode: str = "full",
    delta_zip: bool = False,
    base_export: Path | None = None,
    reuse_zip_manifest: bool = False,
    topology_simplify: str = "safe",
    review_session: str | None = None,
    review_style: str = "balanced",
    dashboard_density: str = "balanced",
    artifact_reduction: str = "balanced",
    change_summary: str = "balanced",
    review_workspace: bool = False,
    generate_review_checklists: bool = False,
    generate_handoff_summary: bool = False,
    ci_smoke: bool = False,
    benchmark_export: bool = False,
    incremental: bool = True,
    requested_video: Path | None = None,
) -> dict:
    if copy_mode != "copy":
        raise ValueError("Only portable copy_mode='copy' is currently supported.")
    if export_profile not in EXPORT_PROFILES:
        raise ValueError(f"Unknown export profile: {export_profile}")
    if dedupe not in {"none", "report", "safe", "aggressive-experimental"}:
        raise ValueError(f"Unknown portable dedupe mode: {dedupe}")
    if validation_tier not in {"quick", "standard", "strict", "extracted_full"}:
        raise ValueError(f"Unknown validation tier: {validation_tier}")
    if generation_mode not in {"eager", "lazy", "hybrid"}:
        raise ValueError(f"Unknown generation mode: {generation_mode}")
    if cache_mode not in {"auto", "refresh", "off"}:
        raise ValueError(f"Unknown cache mode: {cache_mode}")
    if zip_mode not in {"full", "optimized", "delta"}:
        raise ValueError(f"Unknown zip mode: {zip_mode}")
    if topology_simplify not in {"none", "safe", "aggressive"}:
        raise ValueError(f"Unknown topology simplify mode: {topology_simplify}")
    if review_style not in {"executive", "balanced", "audit_dense"}:
        raise ValueError(f"Unknown review style: {review_style}")
    if dashboard_density not in {"compact", "balanced", "expanded"}:
        raise ValueError(f"Unknown dashboard density: {dashboard_density}")
    if artifact_reduction not in {"conservative", "balanced", "aggressive"}:
        raise ValueError(f"Unknown artifact reduction mode: {artifact_reduction}")
    if change_summary not in {"concise", "balanced", "full"}:
        raise ValueError(f"Unknown change summary mode: {change_summary}")
    if validation_tier == "extracted_full":
        validate_extracted = True
    if zip_mode == "delta":
        delta_zip = True
    timings: dict[str, float | None] = {
        "analysis_duration_seconds": None,
        "scan_duration_seconds": None,
        "copy_duration_seconds": None,
        "rewrite_duration_seconds": None,
        "dedupe_duration_seconds": None,
        "governance_generation_duration_seconds": None,
        "index_generation_duration_seconds": None,
        "zip_duration_seconds": None,
        "validation_duration_seconds": None,
        "extracted_validation_duration_seconds": None,
    }
    total_start = time.perf_counter()
    source_root = output_dir.resolve()
    package_root = (dest_root.resolve() if dest_root else source_root / PACKAGE_DIRNAME)
    previous_cache = load_previous_cache(package_root) if incremental and package_root.exists() else {}
    if package_root.exists() and not incremental:
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True, exist_ok=True)
    _prepare_dirs(package_root)
    start = time.perf_counter()
    copied_map, exclusions, copy_stats = _copy_tree(source_root, package_root, include_raw_media=include_raw_media, export_profile=export_profile, previous_cache=previous_cache)
    timings["copy_duration_seconds"] = round(time.perf_counter() - start, 4)
    external_display_assets = _copy_external_display_assets(source_root, package_root, copied_map, include_raw_media=include_raw_media, export_profile=export_profile)
    exclusion_manifest = _write_exclusion_manifest(package_root, exclusions)
    raw_media_excluded_count = exclusion_manifest["summary"]["raw_media_excluded_count"]
    start = time.perf_counter()
    hardening = harden_offline_dashboards(
        package_root,
        source_root,
        copied_map,
        include_raw_media=include_raw_media,
        raw_media_excluded_count=raw_media_excluded_count,
    )
    timings["rewrite_duration_seconds"] = round(time.perf_counter() - start, 4)
    start = time.perf_counter()
    package_scan = _write_asset_dependency_report(package_root)
    timings["scan_duration_seconds"] = round(time.perf_counter() - start, 4)
    files = _build_file_manifest(source_root, package_root, copied_map, package_scan, export_profile)
    artifact_counts = Counter(row["artifact_type"] for row in files)
    total_bytes = sum(row["size_bytes"] for row in files)
    package_id = deterministic_id("PPORT", source_root.as_posix(), len(files), total_bytes, PACKAGE_VERSION)
    manifest = {
        "package_id": package_id,
        "package_version": PACKAGE_VERSION,
        "generator": "video-insight-bundler portable_export_package",
        "generation_timestamp": utc_now_iso(),
        "source_analysis_root": source_root.as_posix(),
        "package_root": package_root.resolve().as_posix(),
        "zip_path": None,
        "raw_media_included": include_raw_media,
        "export_profile": export_profile,
        "validation_tier": validation_tier,
        "generation_mode": generation_mode,
        "cache_mode": cache_mode,
        "zip_mode": zip_mode,
        "reuse_zip_manifest": reuse_zip_manifest,
        "topology_simplify": topology_simplify,
        "selected_review_session": review_session,
        "review_style": review_style,
        "dashboard_density": dashboard_density,
        "artifact_reduction": artifact_reduction,
        "change_summary": change_summary,
        "review_workspace_enabled": review_workspace,
        "review_checklists_enabled": generate_review_checklists,
        "handoff_summary_enabled": generate_handoff_summary,
        "incremental_export_enabled": incremental,
        "requested_video": requested_video.resolve().as_posix() if requested_video else None,
        "raw_media_excluded_count": raw_media_excluded_count,
        "total_files": len(files),
        "total_bytes": total_bytes,
        "artifact_counts_by_type": dict(sorted(artifact_counts.items())),
        "dashboards": [row["package_path"] for row in files if row["artifact_type"] == "dashboard"],
        "html_pages": [row["package_path"] for row in files if Path(row["package_path"]).suffix.lower() in {".html", ".htm"}],
        "graphs": [row["package_path"] for row in files if row["artifact_type"] == "graph"],
        "images": [row["package_path"] for row in files if Path(row["package_path"]).suffix.lower() in IMAGE_EXTENSIONS],
        "boards": [row["package_path"] for row in files if row["artifact_type"] == "board" or any(t in row["package_path"].lower() for t in ("board", "storyboard", "contact_sheet", "giant"))],
        "json_artifacts": [row["package_path"] for row in files if Path(row["package_path"]).suffix.lower() == ".json"],
        "markdown_artifacts": [row["package_path"] for row in files if Path(row["package_path"]).suffix.lower() == ".md"],
        "schemas": [row["package_path"] for row in files if row["artifact_type"] == "schema"],
        "manifests": [row["package_path"] for row in files if row["artifact_type"] == "manifest"],
        "validation_files": [row["package_path"] for row in files if "validation" in row["package_path"].lower()],
        "interpretation_files": [row["package_path"] for row in files if "interpretation" in row["package_path"].lower()],
        "recommendation_files": [row["package_path"] for row in files if "recommendation" in row["package_path"].lower()],
        "evidence_files": [row["package_path"] for row in files if "evidence" in row["package_path"].lower()],
        "governance_files": [row["package_path"] for row in files if "governance" in row["package_path"].lower()],
        "review_files": [row["package_path"] for row in files if "review" in row["package_path"].lower()],
        "timeline_files": [row["package_path"] for row in files if "timeline" in row["package_path"].lower()],
        "snapshot_files": [row["package_path"] for row in files if "snapshot" in row["package_path"].lower()],
        "diff_files": [row["package_path"] for row in files if "diff" in row["package_path"].lower() or "delta" in row["package_path"].lower()],
        "replay_files": [row["package_path"] for row in files if "replay" in row["package_path"].lower()],
        "asset_map": copied_map,
        "external_display_assets_copied": external_display_assets,
        "incremental_copy_summary": copy_stats,
        "path_rewrite_map": hardening.get("rewrite_report", {}).get("rewritten_files", []),
        "excluded_files_summary": exclusion_manifest["summary"],
        "validation_summary": {},
        "files": files,
    }
    write_json(package_root / "portable_package_manifest.json", manifest)
    write_json(package_root / "package_size_report.json", {"analysis_status": "pending", "method": "portable_package_size_v2"})
    write_json(package_root / "package_diff_report.json", {"analysis_status": "pending", "method": "portable_package_diff_v2"})
    write_json(package_root / "portable_package_validation_report.json", {"analysis_status": "pending", "method": "portable_package_validation_v2"})
    write_master_index(package_root, manifest, {"summary": {}, "validation_passed": False})
    (package_root / "PACKAGE_SUMMARY.md").write_text("# Package Summary\n\nPortable package generation in progress.\n", encoding="utf-8")
    start = time.perf_counter()
    validation = validate_portable_package(
        package_root,
        strict=strict,
        allow_provenance_absolute_paths=allow_provenance_absolute_paths,
        raw_media_allowed=include_raw_media,
        export_profile=export_profile,
        zip_created=zip_export,
    )
    timings["validation_duration_seconds"] = round(time.perf_counter() - start, 4)
    integrity = check_portable_integrity(package_root)
    diff_report = write_diff_report(source_root, package_root, copied_map, exclusions)
    privacy_report = _write_privacy_scan(package_root, exclusions)
    size_report = write_size_report(
        package_root,
        source_root=source_root,
        exclusions=exclusions,
        max_file_size_warning_mb=max_file_size_warning_mb,
    )
    start = time.perf_counter()
    dedupe_report = _write_dedupe_report(package_root, dedupe)
    canonical_asset_registry = _write_canonical_asset_registry(package_root, dedupe_report)
    asset_rewrite_validation = _write_asset_rewrite_validation(package_root, dedupe_report)
    timings["dedupe_duration_seconds"] = round(time.perf_counter() - start, 4)
    if dedupe == "safe" and dedupe_report.get("dedupe_savings_bytes", 0):
        _refresh_manifest_file_lists(package_root, manifest)
        validation = validate_portable_package(
            package_root,
            strict=strict,
            allow_provenance_absolute_paths=allow_provenance_absolute_paths,
            raw_media_allowed=include_raw_media,
            export_profile=export_profile,
            zip_created=zip_export,
        )
        size_report = write_size_report(
            package_root,
            source_root=source_root,
            exclusions=exclusions,
            max_file_size_warning_mb=max_file_size_warning_mb,
        )
    build_demo_walkthrough(package_root)
    audit_fallback_links(package_root, source_root, export_profile)
    reachability = analyze_reachability(package_root)
    audit_report = write_export_audit_report(package_root, reachability, size_report, manifest)
    start = time.perf_counter()
    governance = build_dashboard_governance(
        package_root,
        reachability=reachability,
        dedupe_report=dedupe_report,
        consolidation_mode=dashboard_consolidation,
    )
    governance_validation = validate_dashboard_governance(package_root, governance)
    topology = build_topology_graph(package_root, governance)
    topology_simplification = simplify_topology(package_root, topology, mode=topology_simplify) if topology_simplify != "none" else {}
    lifecycle = build_lifecycle_compaction(package_root, governance, topology)
    review_sessions = build_review_sessions(package_root, governance, topology)
    historical = build_historical_continuity(package_root, manifest, governance, topology)
    lazy_generation = build_lazy_generation_registry(package_root, manifest, generation_mode)
    reduction = build_artifact_reduction_report(package_root, governance, mode=artifact_reduction)
    synthetic_dashboards = build_synthetic_dashboards(package_root, governance, reduction, density=dashboard_density)
    change_intelligence = build_change_intelligence(package_root, manifest, diff_report, historical, change_summary=change_summary)
    longitudinal_summary = build_longitudinal_summary(package_root, change_intelligence, historical)
    ux_registries = build_review_ux_registries(package_root, review_style=review_style, dashboard_density=dashboard_density)
    synthesis = build_executive_synthesis(
        package_root,
        manifest,
        validation,
        governance,
        review_style=review_style,
        change_intelligence=change_intelligence,
        reduction=reduction,
    )
    reviewer_workspace = build_reviewer_workspace(
        package_root,
        synthesis["executive_synthesis_report"],
        synthesis["review_priority_registry"],
        review_sessions,
        enabled=review_workspace,
        checklists_enabled=generate_review_checklists or review_workspace,
        handoff_enabled=generate_handoff_summary or review_workspace,
    )
    pre_rc = build_pre_rc_readiness_review(
        package_root,
        validation,
        synthetic_dashboards.get("dashboard_consistency_validation"),
        reduction,
        synthesis.get("executive_synthesis_report"),
    )
    timings["governance_generation_duration_seconds"] = round(time.perf_counter() - start, 4)
    manifest["validation_summary"] = validation.get("summary", {})
    manifest["reachability_summary"] = reachability.get("summary", {})
    manifest["dedupe_summary"] = dedupe_report.get("summary", {})
    manifest["dashboard_governance_summary"] = governance.get("summary", {})
    manifest["dashboard_governance_validation_summary"] = governance_validation.get("summary", {})
    manifest["topology_graph_summary"] = topology.get("topology_graph_registry", {}).get("metrics", {})
    manifest["topology_simplification_summary"] = topology_simplification.get("topology_simplification_report", {}).get("summary", {})
    manifest["lifecycle_compaction_summary"] = lifecycle.get("artifact_lifecycle_compaction_report", {}).get("summary", {})
    manifest["review_session_summary"] = review_sessions.get("review_session_registry", {}).get("summary", {})
    manifest["historical_continuity_summary"] = historical.get("export_lineage_registry", {}).get("summary", {})
    manifest["lazy_generation_summary"] = lazy_generation.get("summary", {})
    manifest["artifact_reduction_summary"] = reduction.get("summary", {})
    manifest["dashboard_consistency_summary"] = synthetic_dashboards.get("dashboard_consistency_validation", {}).get("summary", {})
    manifest["executive_synthesis_summary"] = synthesis.get("executive_synthesis_report", {}).get("summary", {})
    manifest["review_workspace_summary"] = reviewer_workspace.get("review_workspace_registry", {}).get("summary", {})
    manifest["change_intelligence_summary"] = change_intelligence.get("summary", {})
    manifest["longitudinal_summary"] = longitudinal_summary.get("longitudinal_summary_report", {}).get("summary", {})
    manifest["review_ux_summary"] = ux_registries.get("information_density_registry", {}).get("settings", {})
    manifest["pre_rc_readiness_summary"] = pre_rc.get("pre_rc_readiness_report", {}).get("summary", {})
    write_json(package_root / "portable_package_manifest.json", manifest)
    profile_comparison = _write_profile_comparison_report(package_root, source_root, export_profile, include_raw_media)
    start = time.perf_counter()
    write_master_index(package_root, manifest, validation, governance, review_sessions, synthesis, reduction, change_intelligence, pre_rc)
    timings["index_generation_duration_seconds"] = round(time.perf_counter() - start, 4)
    write_package_summary(package_root, manifest, validation, size_report, exclusion_manifest, privacy_report, None, reachability)
    _append_generated_manifest_entries(package_root, manifest)
    incremental_registries = build_incremental_registries(
        package_root,
        source_root=source_root,
        manifest=manifest,
        previous_cache=previous_cache,
        copied_map=copied_map,
        copied_paths=copy_stats.get("copied_paths", []),
        reused_paths=copy_stats.get("reused_paths", []),
        validation_tier=validation_tier,
        export_profile=export_profile,
        generation_mode=generation_mode,
    )
    cache_optimization = build_incremental_cache_optimization(
        package_root,
        manifest=manifest,
        previous_cache=previous_cache,
        export_profile=export_profile,
        validation_tier=validation_tier,
        generation_mode=generation_mode,
        cache_mode=cache_mode,
    )
    manifest["validation_summary"] = validation.get("summary", {})
    manifest["incremental_export_summary"] = incremental_registries.get("incremental_export_registry", {}).get("summary", {})
    manifest["incremental_cache_optimization_summary"] = cache_optimization.get("incremental_cache_optimization_report", {}).get("summary", {})
    write_json(package_root / "portable_package_manifest.json", manifest)
    _write_performance_report(package_root, timings)
    validation = validate_portable_package(
        package_root,
        strict=strict,
        allow_provenance_absolute_paths=allow_provenance_absolute_paths,
        raw_media_allowed=include_raw_media,
        export_profile=export_profile,
        zip_created=zip_export,
    )
    manifest["validation_summary"] = validation.get("summary", {})
    write_json(package_root / "portable_package_manifest.json", manifest)
    write_package_summary(package_root, manifest, validation, size_report, exclusion_manifest, privacy_report, None, reachability)
    write_master_index(package_root, manifest, validation, governance, review_sessions, synthesis, reduction, change_intelligence, pre_rc)
    zip_path = None
    extracted_validation = None
    zip_delta_manifest = None
    if zip_export:
        start = time.perf_counter()
        zip_path = zip_package(package_root, compression_level=compression_level, zip_mode=zip_mode)
        timings["zip_duration_seconds"] = round(time.perf_counter() - start, 4)
    if zip_path:
        size_report = write_size_report(
            package_root,
            source_root=source_root,
            zip_path=zip_path,
            exclusions=exclusions,
            max_file_size_warning_mb=max_file_size_warning_mb,
        )
        manifest["zip_path"] = zip_path.resolve().as_posix()
        manifest["validation_summary"] = validation.get("summary", {})
        write_json(package_root / "portable_package_manifest.json", manifest)
        write_package_summary(package_root, manifest, validation, size_report, exclusion_manifest, privacy_report, zip_path, reachability)
        _append_generated_manifest_entries(package_root, manifest)
        manifest["validation_summary"] = validation.get("summary", {})
        write_json(package_root / "portable_package_manifest.json", manifest)
        validation = validate_portable_package(
            package_root,
            strict=strict,
            allow_provenance_absolute_paths=allow_provenance_absolute_paths,
            raw_media_allowed=include_raw_media,
            export_profile=export_profile,
            zip_created=zip_export,
        )
        manifest["validation_summary"] = validation.get("summary", {})
        write_json(package_root / "portable_package_manifest.json", manifest)
        write_master_index(package_root, manifest, validation, governance, review_sessions, synthesis, reduction, change_intelligence, pre_rc)
        # Refresh zip to include final manifest and summary.
        zip_path = zip_package(package_root, compression_level=compression_level, zip_mode=zip_mode)
        if delta_zip:
            zip_delta_manifest = build_delta_zip(package_root, base_export, compression_level=compression_level)
        size_report = write_size_report(package_root, source_root=source_root, zip_path=zip_path, exclusions=exclusions, max_file_size_warning_mb=max_file_size_warning_mb)
        if validate_extracted:
            start = time.perf_counter()
            extracted_validation = _validate_extracted_zip(
                zip_path,
                strict=strict,
                allow_provenance_absolute_paths=allow_provenance_absolute_paths,
                raw_media_allowed=include_raw_media,
                export_profile=export_profile,
            )
            timings["extracted_validation_duration_seconds"] = round(time.perf_counter() - start, 4)
            write_json(package_root / "validation" / "extracted_zip_validation_report.json", extracted_validation)
            # The extracted copy is the strongest ZIP verification result.
            # Surface it in the canonical report as well so recipients do not
            # see a stale `zip_validated: false` beside a passing extraction.
            validation["zip_validated"] = bool(extracted_validation.get("validation_passed"))
            validation["extracted_zip_validated"] = bool(extracted_validation.get("validation_passed"))
            manifest["validation_summary"] = validation.get("summary", {})
            write_json(package_root / "portable_package_validation_report.json", validation)
            write_json(package_root / "validation" / "portable_package_validation_report.json", validation)
            write_json(package_root / "portable_package_manifest.json", manifest)
    total_duration = round(time.perf_counter() - total_start, 4)
    timings["total_duration_seconds"] = total_duration
    timing_report = {
        "analysis_status": "complete",
        "method": "portable_export_timing_v1",
        "generated_at_utc": utc_now_iso(),
        **timings,
        "slowest_steps": sorted(
            [{"step": key, "duration_seconds": value} for key, value in timings.items() if isinstance(value, (int, float))],
            key=lambda row: row["duration_seconds"],
            reverse=True,
        )[:5],
        "performance_warnings": [],
    }
    write_json(package_root / "portable_export_timing_report.json", timing_report)
    write_json(package_root / "validation" / "portable_export_timing_report.json", timing_report)
    performance_report = _write_performance_report(package_root, timings)
    incremental_performance = write_performance_comparison(package_root, timings, incremental_registries, previous_cache)
    synthesis = build_executive_synthesis(
        package_root,
        manifest,
        validation,
        governance,
        review_style=review_style,
        change_intelligence=change_intelligence,
        reduction=reduction,
    )
    pre_rc = build_pre_rc_readiness_review(
        package_root,
        validation,
        synthetic_dashboards.get("dashboard_consistency_validation"),
        reduction,
        synthesis.get("executive_synthesis_report"),
    )
    manifest["executive_synthesis_summary"] = synthesis.get("executive_synthesis_report", {}).get("summary", {})
    manifest["pre_rc_readiness_summary"] = pre_rc.get("pre_rc_readiness_report", {}).get("summary", {})
    write_json(package_root / "portable_package_manifest.json", manifest)
    write_master_index(package_root, manifest, validation, governance, review_sessions, synthesis, reduction, change_intelligence, pre_rc)
    ci_smoke_report = None
    benchmark_report = None
    release_evidence = None
    if ci_smoke:
        from portable_ci_smoke_suite import run_ci_smoke_suite

        ci_smoke_report = run_ci_smoke_suite(package_root, validation=validation, governance_validation=governance_validation)
    if benchmark_export:
        from portable_benchmark_suite import run_benchmark_suite
        from release_readiness_evidence import build_release_readiness_evidence

        benchmark_report = run_benchmark_suite(package_root, timings=timings, size_report=size_report, topology=topology, incremental=incremental_registries)
        release_evidence = build_release_readiness_evidence(package_root, validation=validation, ci_smoke=ci_smoke_report, benchmark=benchmark_report)
    fallback_audit = audit_fallback_links(package_root, source_root, export_profile)
    manifest["fallback_link_summary"] = fallback_audit["summary"]
    metadata_compaction = compact_package_metadata(package_root)
    _append_generated_manifest_entries(package_root, manifest)
    _refresh_manifest_file_lists(package_root, manifest)
    metadata_aliases = {row["original_package_path"]: row["canonical_path"] for row in metadata_compaction["consolidated_mirrors"]}
    manifest["asset_map"] = {
        source: metadata_aliases.get(rel, rel) for source, rel in manifest.get("asset_map", {}).items()
        if (package_root / metadata_aliases.get(rel, rel)).is_file()
    }
    manifest["metadata_compaction_summary"] = metadata_compaction["summary"]
    validation = validate_portable_package(
        package_root,
        strict=strict,
        allow_provenance_absolute_paths=allow_provenance_absolute_paths,
        raw_media_allowed=include_raw_media,
        export_profile=export_profile,
        zip_created=zip_export,
    )
    # Compaction runs after all page generation; validate and package that final state.
    if ci_smoke:
        ci_smoke_report = run_ci_smoke_suite(package_root, validation=validation, governance_validation=governance_validation)
    if zip_path:
        manifest["zip_path"] = zip_path.resolve().as_posix()
    manifest["validation_summary"] = validation.get("summary", {})
    write_json(package_root / "portable_package_manifest.json", manifest)
    size_report = write_size_report(package_root, source_root=source_root, zip_path=zip_path, exclusions=exclusions, max_file_size_warning_mb=max_file_size_warning_mb)
    write_package_summary(package_root, manifest, validation, size_report, exclusion_manifest, privacy_report, zip_path, reachability)
    # Metadata files include each other in their inventories. Reconcile their byte
    # totals to a stable value, rather than leaving the pre-compaction inventory.
    size_report = _reconcile_package_inventory(package_root, manifest, source_root=source_root, zip_path=zip_path, exclusions=exclusions, max_file_size_warning_mb=max_file_size_warning_mb)
    if zip_path:
        _zip_snapshot(package_root, zip_path, compression_level)
        if validate_extracted:
            extracted_validation = _validate_extracted_zip(zip_path, strict=strict, allow_provenance_absolute_paths=allow_provenance_absolute_paths, raw_media_allowed=include_raw_media, export_profile=export_profile)
            validation["zip_validated"] = bool(extracted_validation.get("validation_passed"))
            validation["extracted_zip_validated"] = bool(extracted_validation.get("validation_passed"))
            write_json(package_root / "validation" / "extracted_zip_validation_report.json", extracted_validation)
            write_json(package_root / "portable_package_validation_report.json", validation)
            write_json(package_root / "validation" / "portable_package_validation_report.json", validation)
            size_report = _reconcile_package_inventory(package_root, manifest, source_root=source_root, zip_path=zip_path, exclusions=exclusions, max_file_size_warning_mb=max_file_size_warning_mb)
            # Include the verification evidence without generating more assembly reports.
            _zip_snapshot(package_root, zip_path, compression_level)
    _write_verification_summary(source_root, package_root, validation, manifest, zip_path)
    return {
        "package_root": package_root,
        "zip_path": zip_path,
        "manifest": manifest,
        "validation": validation,
        "integrity": integrity,
        "diff_report": diff_report,
        "size_report": size_report,
        "privacy_report": privacy_report,
        "exclusion_manifest": exclusion_manifest,
        "dedupe_report": dedupe_report,
        "canonical_asset_registry": canonical_asset_registry,
        "asset_rewrite_validation": asset_rewrite_validation,
        "reachability_report": reachability,
        "audit_report": audit_report,
        "dashboard_governance": governance,
        "dashboard_governance_validation": governance_validation,
        "topology_graph": topology,
        "topology_simplification": topology_simplification,
        "lifecycle_compaction": lifecycle,
        "review_sessions": review_sessions,
        "historical_continuity": historical,
        "lazy_generation": lazy_generation,
        "artifact_reduction_report": reduction,
        "synthetic_dashboards": synthetic_dashboards,
        "executive_synthesis": synthesis,
        "reviewer_workspace": reviewer_workspace,
        "change_intelligence_report": change_intelligence,
        "longitudinal_summary": longitudinal_summary,
        "review_ux_registries": ux_registries,
        "pre_rc_readiness": pre_rc,
        "incremental_registries": incremental_registries,
        "incremental_cache_optimization": cache_optimization,
        "zip_delta_manifest": zip_delta_manifest,
        "profile_comparison_report": profile_comparison,
        "timing_report": timing_report,
        "performance_report": performance_report,
        "incremental_performance_comparison": incremental_performance,
        "ci_smoke_report": ci_smoke_report,
        "benchmark_report": benchmark_report,
        "release_readiness_evidence": release_evidence,
        "metadata_compaction": metadata_compaction,
        "extracted_validation": extracted_validation,
        "asset_dependency_report": package_root / "manifests" / "asset_dependency_report.json",
        "validation_report": package_root / "portable_package_validation_report.json",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a portable self-contained review package from a Corpus_analysis output tree.")
    parser.add_argument("--source", help="Source Corpus_analysis directory.")
    parser.add_argument("--dest", help="Destination portable package root. Defaults to <source>/portable_review_package.")
    parser.add_argument("--zip", action="store_true", help="Create portable_review_package.zip next to the package root.")
    parser.add_argument("--export-profile", default="review", choices=sorted(EXPORT_PROFILES), help="Package profile. Default review.")
    parser.add_argument("--portable-dedupe", default="report", choices=["none", "report", "safe", "aggressive-experimental"], help="Duplicate handling mode. Default report.")
    parser.add_argument("--dashboard-consolidation", default="grouped", choices=["none", "grouped", "aggressive"], help="Dashboard drilldown consolidation mode. Default grouped.")
    parser.add_argument("--compression-level", type=int, default=8, choices=range(0, 10), metavar="0-9", help="Zip compression level. Default 8.")
    parser.add_argument("--validate-extracted", action="store_true", help="Extract the zip to a temp folder and validate the extracted copy.")
    parser.add_argument("--validation-tier", default="standard", choices=["quick", "standard", "strict", "extracted_full"], help="Validation tier. Default standard.")
    parser.add_argument("--generation-mode", default="hybrid", choices=["eager", "lazy", "hybrid"], help="Analytical generation mode. Default hybrid.")
    parser.add_argument("--cache-mode", default="auto", choices=["auto", "refresh", "off"], help="Incremental cache policy. Default auto.")
    parser.add_argument("--zip-mode", default="full", choices=["full", "optimized", "delta"], help="Zip assembly mode. Default full.")
    parser.add_argument("--delta-zip", action="store_true", help="Generate a sidecar delta zip with changed/new files.")
    parser.add_argument("--base-export", help="Base portable package folder for delta comparison.")
    parser.add_argument("--reuse-zip-manifest", action="store_true", help="Reuse prior zip manifest for planning when available.")
    parser.add_argument("--topology-simplify", default="safe", choices=["none", "safe", "aggressive"], help="Topology simplification mode. Default safe.")
    parser.add_argument("--review-session", choices=["executive", "governance", "recommendation", "evidence", "interpretation", "timeline", "audit", "diff"], help="Preferred guided review pathway.")
    parser.add_argument("--review-style", default="balanced", choices=["executive", "balanced", "audit_dense"], help="Review synthesis style. Default balanced.")
    parser.add_argument("--dashboard-density", default="balanced", choices=["compact", "balanced", "expanded"], help="Dashboard information density. Default balanced.")
    parser.add_argument("--artifact-reduction", default="balanced", choices=["conservative", "balanced", "aggressive"], help="Artifact reduction mode. Default balanced.")
    parser.add_argument("--change-summary", default="balanced", choices=["concise", "balanced", "full"], help="Change summary detail. Default balanced.")
    parser.add_argument("--review-workspace", action="store_true", help="Generate static review workspace pages.")
    parser.add_argument("--generate-review-checklists", action="store_true", help="Generate reviewer checklists.")
    parser.add_argument("--generate-handoff-summary", action="store_true", help="Generate static handoff summary templates.")
    parser.add_argument("--ci-smoke", action="store_true", help="Generate portable CI smoke report.")
    parser.add_argument("--benchmark-export", action="store_true", help="Generate portable benchmark report.")
    parser.add_argument("--disable-incremental", action="store_true", help="Disable cache-aware incremental export reuse.")
    parser.add_argument("--clean-old-exports", action="store_true", help="Remove stale portable packages/zips/temp exports from --source.")
    parser.add_argument("--clean-dry-run", action="store_true", help="List stale portable artifacts without deleting them.")
    parser.add_argument("--include-raw-media", action="store_true", help="Explicitly include raw media in media/. Default excludes raw media.")
    parser.add_argument("--strict", default="true", choices=["true", "false"], help="Whether validation warnings should use strict checks. Default true.")
    parser.add_argument("--allow-provenance-absolute-paths", default="true", choices=["true", "false"], help="Allow absolute paths only as provenance metadata. Default true.")
    parser.add_argument("--max-file-size-warning-mb", type=float, default=100.0)
    parser.add_argument("--copy-mode", default="copy", choices=["copy"])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.clean_old_exports or args.clean_dry_run:
        if not args.source:
            print("--source is required for cleanup.", file=sys.stderr)
            return 2
        report = clean_old_exports(Path(args.source), dry_run=args.clean_dry_run or not args.clean_old_exports)
        print(f"Portable cleanup report: {Path(args.source).resolve() / 'portable_cleanup_report.json'}")
        print(f"Candidates: {report['candidate_count']}")
        print(f"Removed: {report['removed_count']}")
        return 0
    if not args.source:
        print("--source is required.", file=sys.stderr)
        return 2
    result = build_portable_package(
        Path(args.source),
        Path(args.dest) if args.dest else None,
        zip_export=args.zip,
        include_raw_media=args.include_raw_media,
        strict=args.strict == "true",
        allow_provenance_absolute_paths=args.allow_provenance_absolute_paths == "true",
        max_file_size_warning_mb=args.max_file_size_warning_mb,
        copy_mode=args.copy_mode,
        export_profile=args.export_profile,
        dedupe=args.portable_dedupe,
        dashboard_consolidation=args.dashboard_consolidation,
        compression_level=args.compression_level,
        validate_extracted=args.validate_extracted,
        validation_tier=args.validation_tier,
        generation_mode=args.generation_mode,
        cache_mode=args.cache_mode,
        zip_mode=args.zip_mode,
        delta_zip=args.delta_zip,
        base_export=Path(args.base_export).expanduser().resolve() if args.base_export else None,
        reuse_zip_manifest=args.reuse_zip_manifest,
        topology_simplify=args.topology_simplify,
        review_session=args.review_session,
        review_style=args.review_style,
        dashboard_density=args.dashboard_density,
        artifact_reduction=args.artifact_reduction,
        change_summary=args.change_summary,
        review_workspace=args.review_workspace,
        generate_review_checklists=args.generate_review_checklists,
        generate_handoff_summary=args.generate_handoff_summary,
        ci_smoke=args.ci_smoke,
        benchmark_export=args.benchmark_export,
        incremental=not args.disable_incremental,
    )
    validation = result["validation"]
    size_summary = result["size_report"].get("summary", {})
    print("Portable export complete.")
    print("")
    print(f"Open first:\n{(Path(result['package_root']) / 'index.html').resolve()}")
    if result.get("zip_path"):
        print(f"\nSend this zip:\n{Path(result['zip_path']).resolve()}")
    print("")
    print(f"Profile:\n{args.export_profile}")
    print(f"\nRaw video included:\n{'yes' if args.include_raw_media else 'no'}")
    print(f"\nValidation:\n{'passed' if validation.get('validation_passed') else 'failed'}")
    print(f"\nBroken links:\n{validation.get('broken_link_count')}")
    print(f"\nMissing assets:\n{validation.get('missing_asset_count')}")
    print(f"\nPackage size:\n{round((size_summary.get('total_package_size_bytes') or 0) / (1024 * 1024), 2)} MB")
    print(f"\nZip size:\n{round((size_summary.get('zip_size_bytes') or 0) / (1024 * 1024), 2) if size_summary.get('zip_size_bytes') is not None else 'not generated'} MB")
    return 0 if result["validation"].get("validation_passed") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
