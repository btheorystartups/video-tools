"""Deterministic governance continuity navigation."""

from __future__ import annotations

from phase43_recall_common import phase43_artifact, relation_rows, render_recall_page, stable_row_id


def build_governance_continuity_registry(outputs: dict) -> dict:
    rows = relation_rows(outputs, "governance_continuity", "governance", 10)
    artifact = phase43_artifact("deterministic_governance_continuity_navigation_v1")
    artifact.update({"governance_continuity_registry_id": stable_row_id("GCONTREG", [row["relation_id"] for row in rows]), "governance_paths": rows, "summary": {"governance_continuity_count": len(rows)}})
    return artifact


def render_governance_continuity_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("governance_continuity_registry") or {}).get("governance_paths") or []
    return render_recall_page("Governance Continuity Dashboard", "governance_continuity_dashboard.html", rows, ["from_event_id", "to_event_id", "summary", "navigation_hint"], "relation_id", [("Governance links", len(rows))])
