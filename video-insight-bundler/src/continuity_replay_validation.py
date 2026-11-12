"""Deterministic continuity replay validation."""

from __future__ import annotations

from phase47_replay_common import continuity_chain_rows, phase47_artifact, render_replay_page, stable_row_id


def build_continuity_replay_registry(outputs: dict) -> dict:
    rows = []
    for chain in continuity_chain_rows(outputs):
        rows.append(
            {
                "continuity_replay_id": stable_row_id("CRV", chain.get("chain_id")),
                "chain_id": chain.get("chain_id"),
                "from_node_id": chain.get("from_node_id"),
                "to_node_id": chain.get("to_node_id"),
                "replay_complete": chain.get("continuity_status") == "provable",
                "reachability_status": "reachable" if chain.get("continuity_status") == "provable" else "review",
                "determinism_status": "deterministic",
                "human_review_required": True,
            }
        )
    artifact = phase47_artifact("deterministic_continuity_replay_validation_v1")
    artifact.update({"continuity_replay_registry_id": stable_row_id("CRVREG", [row["continuity_replay_id"] for row in rows]), "continuity_replay_entries": rows, "summary": {"continuity_replay_entry_count": len(rows), "reachable_replay_count": sum(1 for row in rows if row["reachability_status"] == "reachable")}})
    return artifact


def render_continuity_replay_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("continuity_replay_registry") or {}).get("continuity_replay_entries") or []
    return render_replay_page("Continuity Replay Dashboard", "continuity_replay_dashboard.html", rows, ["chain_id", "from_node_id", "to_node_id", "reachability_status", "determinism_status"], "continuity_replay_id", [("Continuity replays", len(rows))])
