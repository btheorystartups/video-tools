"""Deterministic operational-state transition maps."""

from __future__ import annotations

from phase43_recall_common import phase43_artifact, render_recall_page, stable_row_id, transition_rows


def build_operational_state_transition_registry(outputs: dict) -> dict:
    rows = transition_rows(outputs, 18)
    artifact = phase43_artifact("deterministic_operational_state_transition_map_v1")
    artifact.update({"operational_state_transition_registry_id": stable_row_id("OSTREG", [row["transition_id"] for row in rows]), "state_transitions": rows, "summary": {"state_transition_count": len(rows)}})
    return artifact


def render_operational_transition_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("operational_state_transition_registry") or {}).get("state_transitions") or []
    return render_recall_page("Operational Transition Dashboard", "operational_transition_dashboard.html", rows, ["transition_type", "direction", "from_value", "to_value", "summary"], "transition_id", [("Transitions", len(rows))])
