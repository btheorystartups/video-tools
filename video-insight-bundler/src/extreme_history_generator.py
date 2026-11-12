"""Deterministic extreme synthetic history generator."""

from __future__ import annotations

from phase47_replay_common import phase47_artifact, render_replay_page, replay_edges, replay_routes, stable_row_id


def build_extreme_history_registry(outputs: dict) -> dict:
    base_edges = max(1, len(replay_edges(outputs)))
    base_routes = max(1, len(replay_routes()))
    specs = [("continuity_chain", base_edges * 100), ("escalation_history", base_edges * 60), ("governance_history", base_edges * 80), ("pagination_chain", base_routes * 250), ("dashboard_routing", base_routes * 180), ("interaction_graph", base_edges * base_routes)]
    rows = [
        {
            "extreme_history_id": stable_row_id("EHG", name, load),
            "history_type": name,
            "synthetic_entry_count": int(load),
            "generation_basis": "deterministic_count_expansion",
            "history_generation_status": "generated",
            "human_review_required": True,
        }
        for name, load in specs
    ]
    artifact = phase47_artifact("deterministic_extreme_history_generation_v1")
    artifact.update({"extreme_history_registry_id": stable_row_id("EHGREG", [row["extreme_history_id"] for row in rows]), "extreme_history_entries": rows, "summary": {"extreme_history_entry_count": len(rows), "synthetic_total_entry_count": sum(row["synthetic_entry_count"] for row in rows)}})
    return artifact


def render_extreme_history_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("extreme_history_registry") or {}).get("extreme_history_entries") or []
    return render_replay_page("Extreme History Dashboard", "extreme_history_dashboard.html", rows, ["history_type", "synthetic_entry_count", "generation_basis", "history_generation_status"], "extreme_history_id", [("Extreme histories", len(rows)), ("Synthetic entries", sum(row.get("synthetic_entry_count") or 0 for row in rows))])
