"""Deterministic sortable static table registry."""

from __future__ import annotations

from phase45_interaction_common import all_interaction_events, operational_score, phase45_artifact, render_interaction_page, stable_row_id


def build_sortable_table_registry(outputs: dict) -> dict:
    rows = []
    sort_specs = ["continuity", "escalation", "governance", "survivability", "workload"]
    for event in all_interaction_events(outputs, 72):
        focus = event.get("focus") or "operational"
        rows.append(
            {
                "sortable_table_entry_id": stable_row_id("STBL", event.get("source_event_id"), focus),
                "source_event_id": event.get("source_event_id"),
                "focus": focus,
                "continuity_sort": operational_score(event),
                "escalation_sort": 1 if focus == "escalation" else 0,
                "governance_sort": 1 if focus == "governance" else 0,
                "survivability_sort": 1 if focus == "survivability" else 0,
                "workload_sort": 1 if focus in {"workload", "throughput"} else 0,
                "sortable_columns": sort_specs,
                "human_review_required": True,
            }
        )
    rows = sorted(rows, key=lambda row: (-row["continuity_sort"], row["focus"], row["source_event_id"]))
    artifact = phase45_artifact("deterministic_sortable_static_tables_v1")
    artifact.update({"sortable_table_registry_id": stable_row_id("STBLREG", [row["sortable_table_entry_id"] for row in rows]), "sortable_tables": rows, "summary": {"sortable_table_count": len(rows), "sortable_column_count": len(sort_specs)}})
    return artifact


def render_sortable_tables_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("sortable_table_registry") or {}).get("sortable_tables") or []
    return render_interaction_page("Sortable Tables Dashboard", "sortable_tables_dashboard.html", rows, ["focus", "source_event_id", "continuity_sort", "escalation_sort", "governance_sort", "survivability_sort", "workload_sort"], "sortable_table_entry_id", [("Sortable rows", len(rows))])
