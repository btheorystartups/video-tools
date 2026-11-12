"""Deterministic escalation continuity navigation."""

from __future__ import annotations

from phase43_recall_common import phase43_artifact, relation_rows, render_recall_page, stable_row_id


def build_escalation_continuity_registry(outputs: dict) -> dict:
    rows = relation_rows(outputs, "escalation_continuity", "escalation", 10)
    artifact = phase43_artifact("deterministic_escalation_continuity_navigation_v1")
    artifact.update({"escalation_continuity_registry_id": stable_row_id("ECONTREG", [row["relation_id"] for row in rows]), "escalation_paths": rows, "summary": {"escalation_continuity_count": len(rows)}})
    return artifact


def render_escalation_continuity_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("escalation_continuity_registry") or {}).get("escalation_paths") or []
    return render_recall_page("Escalation Continuity Dashboard", "escalation_continuity_dashboard.html", rows, ["from_event_id", "to_event_id", "summary", "navigation_hint"], "relation_id", [("Escalation links", len(rows))])
