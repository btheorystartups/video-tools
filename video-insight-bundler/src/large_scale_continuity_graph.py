"""Deterministic large-scale continuity graph fixtures."""

from __future__ import annotations

from phase47_replay_common import continuity_chain_rows, phase47_artifact, render_replay_page, stable_row_id


def build_large_scale_continuity_registry(outputs: dict) -> dict:
    chains = continuity_chain_rows(outputs, 120)
    rows = []
    for multiplier in [10, 50, 100, 250]:
        rows.append(
            {
                "large_scale_continuity_id": stable_row_id("LSC", multiplier, len(chains)),
                "fixture_scale": multiplier,
                "synthetic_node_count": max(1, len(chains)) * multiplier,
                "synthetic_edge_count": max(1, len(chains)) * max(1, multiplier - 1),
                "continuity_graph_status": "survivable",
                "human_review_required": True,
            }
        )
    artifact = phase47_artifact("deterministic_large_scale_continuity_graph_v1")
    artifact.update({"large_scale_continuity_registry_id": stable_row_id("LSCREG", [row["large_scale_continuity_id"] for row in rows]), "large_scale_continuity_entries": rows, "summary": {"large_scale_continuity_entry_count": len(rows)}})
    return artifact


def render_continuity_graph_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("large_scale_continuity_registry") or {}).get("large_scale_continuity_entries") or []
    return render_replay_page("Continuity Graph Dashboard", "continuity_graph_dashboard.html", rows, ["fixture_scale", "synthetic_node_count", "synthetic_edge_count", "continuity_graph_status"], "large_scale_continuity_id", [("Graph fixtures", len(rows))])
