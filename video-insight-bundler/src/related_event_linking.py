"""Deterministic related event linking."""

from __future__ import annotations

from phase43_recall_common import RECALL_LENSES, phase43_artifact, relation_rows, render_recall_page, stable_row_id


def build_related_event_registry(outputs: dict) -> dict:
    rows = []
    for focus, _keywords in RECALL_LENSES:
        rows.extend(relation_rows(outputs, f"related_{focus}_events", focus, 5))
    artifact = phase43_artifact("deterministic_related_event_linking_v1")
    artifact.update({"related_event_registry_id": stable_row_id("RELREG", [row["relation_id"] for row in rows]), "related_events": rows, "summary": {"related_event_count": len(rows)}})
    return artifact


def render_related_event_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("related_event_registry") or {}).get("related_events") or []
    return render_recall_page("Related Event Dashboard", "related_event_dashboard.html", rows, ["relation_type", "focus", "from_event_id", "to_event_id"], "relation_id", [("Related events", len(rows))])
