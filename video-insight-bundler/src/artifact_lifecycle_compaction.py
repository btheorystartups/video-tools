"""Lifecycle compaction, stale archival, and lazy generation registries."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from stability import deterministic_id, utc_now_iso, write_json


LIFECYCLE_ACTIONS = [
    "active",
    "archived",
    "compressed",
    "hidden",
    "merged",
    "superseded",
    "retained_for_audit",
    "retained_for_replay",
    "retained_for_snapshot",
]


def build_lifecycle_compaction(package_root: Path, governance: dict | None, topology: dict | None) -> dict:
    root = package_root.resolve()
    rows = (governance or {}).get("dashboard_governance_registry", {}).get("dashboards", [])
    graph_metrics = (topology or {}).get("topology_graph_registry", {}).get("metrics", {})
    superseded = []
    stale = []
    pruning = []
    compactions = []
    grouped_drilldowns: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        path = row.get("package_path")
        if not path:
            continue
        action = "active"
        reason = "active review artifact"
        if row.get("superseded_by"):
            action = "superseded"
            reason = "duplicate artifact has a canonical replacement"
            superseded.append({"artifact_path": path, "superseded_by": row.get("superseded_by"), "collapse_action": "redirect_to_canonical"})
        elif row.get("orphaned") and row.get("lifecycle_state") not in {"audit"}:
            action = "archived"
            reason = "unreachable non-audit artifact"
            stale.append({"artifact_path": path, "archive_action": "hide_from_navigation", "reason": reason})
        elif row.get("visibility") == "hidden":
            action = "hidden"
            reason = "low-priority drilldown or internal artifact"
        elif row.get("lifecycle_state") == "audit":
            action = "retained_for_audit"
            reason = "audit material retained without primary navigation"
        if row.get("drilldown_depth", 0) >= 2:
            grouped_drilldowns[f"{row.get('category')}::{row.get('subcategory')}"].append(path)
        compactions.append(
            {
                "artifact_path": path,
                "lifecycle_action": action,
                "reason": reason,
                "retention_policy": _retention_policy(row, action),
                "expiration_policy": _expiration_policy(row, action),
            }
        )
        if action in {"archived", "hidden", "superseded"}:
            pruning.append({"artifact_path": path, "recommended_pruning_action": action, "reason": reason})
    drilldown_consolidation = [
        {
            "collection_id": deterministic_id("DRILL", key),
            "collection_key": key,
            "source_drilldowns": sorted(paths),
            "consolidation_action": "merge_into_clustered_drilldown_index",
        }
        for key, paths in grouped_drilldowns.items()
        if len(paths) > 1
    ]
    compaction_report = {
        "analysis_status": "complete",
        "method": "artifact_lifecycle_compaction_v63",
        "generated_at_utc": utc_now_iso(),
        "lifecycle_actions": LIFECYCLE_ACTIONS,
        "artifact_actions": compactions,
        "lineage_compaction": {
            "strategy": "retain canonical summary plus audit/replay/snapshot leaves",
            "compressed_lineage_candidate_count": sum(1 for row in compactions if row["lifecycle_action"] in {"compressed", "superseded", "hidden"}),
        },
        "delta_aggregation": {
            "strategy": "cluster low-priority delta and diff drilldowns by category",
            "aggregated_collection_count": len(drilldown_consolidation),
        },
        "drilldown_consolidation": drilldown_consolidation,
        "summary": {
            "artifact_count": len(compactions),
            "archived_count": sum(1 for row in compactions if row["lifecycle_action"] == "archived"),
            "hidden_count": sum(1 for row in compactions if row["lifecycle_action"] == "hidden"),
            "superseded_count": sum(1 for row in compactions if row["lifecycle_action"] == "superseded"),
            "retained_for_audit_count": sum(1 for row in compactions if row["lifecycle_action"] == "retained_for_audit"),
            "topology_cycle_count": graph_metrics.get("cycle_count", 0),
        },
    }
    pruning_report = {
        "analysis_status": "complete",
        "method": "topology_pruning_report_v63",
        "generated_at_utc": utc_now_iso(),
        "pruning_candidates": pruning,
        "topology_pruning_policy": {
            "prune_unreachable_non_audit": True,
            "hide_low_priority_drilldowns": True,
            "retain_audit_replay_snapshot": True,
            "archive_old_topology_generations": True,
        },
        "summary": {
            "pruning_candidate_count": len(pruning),
            "orphan_reduction_candidate_count": sum(1 for row in pruning if row["recommended_pruning_action"] == "archived"),
            "cycle_reduction_candidate_count": graph_metrics.get("cycle_count", 0),
        },
    }
    superseded_registry = {
        "analysis_status": "complete",
        "method": "superseded_artifact_registry_v63",
        "generated_at_utc": utc_now_iso(),
        "superseded_artifacts": superseded,
        "summary": {"superseded_artifact_count": len(superseded)},
    }
    stale_registry = {
        "analysis_status": "complete",
        "method": "stale_artifact_archive_registry_v63",
        "generated_at_utc": utc_now_iso(),
        "stale_artifacts": stale,
        "summary": {"stale_artifact_count": len(stale)},
    }
    for name, payload in [
        ("artifact_lifecycle_compaction_report.json", compaction_report),
        ("topology_pruning_report.json", pruning_report),
        ("superseded_artifact_registry.json", superseded_registry),
        ("stale_artifact_archive_registry.json", stale_registry),
    ]:
        write_json(root / name, payload)
        write_json(root / "governance" / name, payload)
    return {
        "artifact_lifecycle_compaction_report": compaction_report,
        "topology_pruning_report": pruning_report,
        "superseded_artifact_registry": superseded_registry,
        "stale_artifact_archive_registry": stale_registry,
    }


def build_lazy_generation_registry(package_root: Path, manifest: dict, mode: str = "hybrid") -> dict:
    if mode not in {"eager", "lazy", "hybrid"}:
        raise ValueError(f"Unknown lazy generation mode: {mode}")
    entries = []
    for row in manifest.get("files") or []:
        rel = row.get("package_path")
        if not rel:
            continue
        lower = rel.lower()
        priority = _generation_priority(row)
        if mode == "eager":
            pre_generated = True
        elif mode == "lazy":
            pre_generated = priority >= 85
        else:
            pre_generated = priority >= 45 and not any(token in lower for token in ("deep", "drilldown", "debug", "trace"))
        entries.append(
            {
                "artifact_path": rel,
                "generated_on_demand": not pre_generated,
                "pre_generated": pre_generated,
                "generation_cost": _cost(row),
                "access_frequency_estimate": _access_frequency(row),
                "last_accessed": None,
                "generation_priority": priority,
            }
        )
    registry = {
        "analysis_status": "complete",
        "method": "lazy_generation_registry_v62_v66",
        "generated_at_utc": utc_now_iso(),
        "generation_mode": mode,
        "artifacts": entries,
        "summary": {
            "artifact_count": len(entries),
            "pre_generated_count": sum(1 for row in entries if row["pre_generated"]),
            "generated_on_demand_count": sum(1 for row in entries if row["generated_on_demand"]),
            "estimated_deferred_generation_cost": sum(row["generation_cost"] for row in entries if row["generated_on_demand"]),
        },
    }
    write_json(package_root / "lazy_generation_registry.json", registry)
    write_json(package_root / "governance" / "lazy_generation_registry.json", registry)
    return registry


def _retention_policy(row: dict, action: str) -> str:
    if action == "retained_for_audit":
        return "retain_for_audit"
    if "replay" in str(row.get("package_path", "")).lower():
        return "retained_for_replay"
    if "snapshot" in str(row.get("package_path", "")).lower():
        return "retained_for_snapshot"
    if action in {"archived", "hidden", "superseded"}:
        return "retain_summary_hide_detail"
    return "active"


def _expiration_policy(row: dict, action: str) -> str:
    if action in {"retained_for_audit", "retained_for_replay", "retained_for_snapshot"}:
        return "no_expiration_without_manual_approval"
    if action in {"archived", "superseded"}:
        return "eligible_after_two_successor_exports"
    return "active_until_replaced"


def _generation_priority(row: dict) -> int:
    score = 30
    rel = str(row.get("package_path") or "").lower()
    if rel == "index.html" or rel.endswith("dashboard.html"):
        score += 50
    if row.get("human_review_value") == "high":
        score += 25
    if any(token in rel for token in ("governance", "recommendation", "validation", "summary")):
        score += 15
    if any(token in rel for token in ("drilldown", "debug", "trace", "deep", "raw")):
        score -= 30
    return max(0, min(100, score))


def _cost(row: dict) -> int:
    return max(1, min(100, int((row.get("size_bytes") or 0) / 4096) + (20 if str(row.get("package_path", "")).endswith(".json") else 10)))


def _access_frequency(row: dict) -> str:
    priority = _generation_priority(row)
    if priority >= 75:
        return "high"
    if priority >= 45:
        return "medium"
    return "low"
