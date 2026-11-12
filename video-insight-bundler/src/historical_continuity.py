"""Export lineage and corpus evolution registries."""

from __future__ import annotations

import json
from pathlib import Path

from stability import deterministic_id, utc_now_iso, write_json


def build_historical_continuity(package_root: Path, manifest: dict, governance: dict | None, topology: dict | None) -> dict:
    root = package_root.resolve()
    previous = _load_previous(root)
    package_id = manifest.get("package_id") or deterministic_id("PPORT", root.as_posix())
    now = utc_now_iso()
    history_entry = {
        "package_id": package_id,
        "generated_at_utc": manifest.get("generation_timestamp") or now,
        "export_profile": manifest.get("export_profile"),
        "package_root": manifest.get("package_root"),
        "zip_path": manifest.get("zip_path"),
        "total_files": manifest.get("total_files"),
        "total_bytes": manifest.get("total_bytes"),
        "topology_metrics": (topology or {}).get("topology_graph_registry", {}).get("metrics", {}),
        "governance_summary": (governance or {}).get("summary", {}),
    }
    prior_history = previous.get("history") or []
    history = [*prior_history, history_entry]
    lineage = {
        "analysis_status": "complete",
        "method": "export_lineage_registry_v66",
        "generated_at_utc": now,
        "package_lineage_id": deterministic_id("EXPLIN", [row.get("package_id") for row in history]),
        "current_package_id": package_id,
        "previous_package_id": prior_history[-1].get("package_id") if prior_history else None,
        "history": history,
        "comparison_supported": True,
        "summary": {"generation_count": len(history), "has_previous_export": bool(prior_history)},
    }
    evolution = {
        "analysis_status": "complete",
        "method": "corpus_evolution_registry_v66",
        "generated_at_utc": now,
        "current_package_id": package_id,
        "corpus_evolution_summaries": _evolution_summaries(history),
        "recommendation_evolution_supported": True,
        "governance_evolution_supported": True,
        "topology_evolution_supported": True,
        "reviewer_pathway_evolution_supported": True,
        "summary": {
            "generation_count": len(history),
            "file_count_delta": _delta(history, "total_files"),
            "byte_delta": _delta(history, "total_bytes"),
        },
    }
    historical_index = {
        "analysis_status": "complete",
        "method": "historical_export_index_v66",
        "generated_at_utc": now,
        "exports": history,
        "cross_export_comparison": {
            "compare_exports_over_time": True,
            "trace_recommendation_evolution": True,
            "trace_governance_evolution": True,
            "trace_topology_evolution": True,
            "trace_reviewer_pathway_changes": True,
        },
    }
    longitudinal = {
        "analysis_status": "complete",
        "method": "longitudinal_review_registry_v66",
        "generated_at_utc": now,
        "review_continuity": [
            {
                "package_id": row.get("package_id"),
                "recommended_resume_context": "continue_last_review_session" if index else "start_executive_review_session",
                "reviewer_pathway_change": _pathway_change(history[index - 1], row) if index else "initial_export",
            }
            for index, row in enumerate(history)
        ],
        "summary": {"review_continuity_entry_count": len(history)},
    }
    for name, payload in [
        ("export_lineage_registry.json", lineage),
        ("corpus_evolution_registry.json", evolution),
        ("historical_export_index.json", historical_index),
        ("longitudinal_review_registry.json", longitudinal),
    ]:
        write_json(root / name, payload)
        write_json(root / "governance" / name, payload)
    return {
        "export_lineage_registry": lineage,
        "corpus_evolution_registry": evolution,
        "historical_export_index": historical_index,
        "longitudinal_review_registry": longitudinal,
    }


def _load_previous(root: Path) -> dict:
    path = root / "export_lineage_registry.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _delta(history: list[dict], key: str) -> int:
    if len(history) < 2:
        return 0
    return int(history[-1].get(key) or 0) - int(history[-2].get(key) or 0)


def _evolution_summaries(history: list[dict]) -> list[dict]:
    summaries = []
    for index, row in enumerate(history):
        previous = history[index - 1] if index else {}
        summaries.append(
            {
                "package_id": row.get("package_id"),
                "generation_index": index + 1,
                "file_count_delta": int(row.get("total_files") or 0) - int(previous.get("total_files") or 0),
                "byte_delta": int(row.get("total_bytes") or 0) - int(previous.get("total_bytes") or 0),
                "topology_node_delta": int((row.get("topology_metrics") or {}).get("node_count") or 0)
                - int((previous.get("topology_metrics") or {}).get("node_count") or 0),
                "governance_orphan_delta": int((row.get("governance_summary") or {}).get("orphan_count") or 0)
                - int((previous.get("governance_summary") or {}).get("orphan_count") or 0),
            }
        )
    return summaries


def _pathway_change(previous: dict, current: dict) -> str:
    prev_count = int((previous.get("topology_metrics") or {}).get("node_count") or 0)
    cur_count = int((current.get("topology_metrics") or {}).get("node_count") or 0)
    if cur_count > prev_count:
        return "expanded_review_surface"
    if cur_count < prev_count:
        return "compacted_review_surface"
    return "stable_review_surface"
