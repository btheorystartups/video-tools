"""Deterministic contextual operational stitching."""

from __future__ import annotations

from phase43_recall_common import phase43_artifact, relation_rows, render_recall_page, stable_row_id


def build_contextual_stitching_registry(outputs: dict) -> dict:
    rows = []
    for relation_type, focus in [
        ("escalation_chain", "escalation"),
        ("governance_transition", "governance"),
        ("survivability_change", "survivability"),
        ("ambiguity_cluster", "ambiguity"),
        ("rebuild_cost_evolution", "throughput"),
        ("queue_growth_progression", "workload"),
    ]:
        rows.extend(relation_rows(outputs, relation_type, focus, 6))
    artifact = phase43_artifact("deterministic_contextual_operational_stitching_v1")
    artifact.update({"contextual_stitching_registry_id": stable_row_id("CSTREG", [row["relation_id"] for row in rows]), "stitches": rows, "summary": {"stitch_count": len(rows)}})
    return artifact


def render_contextual_stitching_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("contextual_stitching_registry") or {}).get("stitches") or []
    return render_recall_page("Contextual Stitching Dashboard", "contextual_stitching_dashboard.html", rows, ["relation_type", "focus", "from_event_id", "to_event_id", "navigation_hint"], "relation_id", [("Stitches", len(rows))])
