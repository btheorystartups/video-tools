"""Deterministic compressed recall navigation."""

from __future__ import annotations

from phase43_recall_common import events_for_focus, phase43_artifact, render_recall_page, source_ids, stable_row_id


def build_compressed_recall_navigation_registry(outputs: dict) -> dict:
    specs = [
        ("top_historical_shifts", "throughput"),
        ("top_unresolved_states", "governance"),
        ("top_regressions", "workload"),
        ("top_survivability_changes", "survivability"),
        ("top_governance_periods", "governance"),
        ("top_escalation_periods", "escalation"),
    ]
    rows = []
    for recall_type, focus in specs:
        events = events_for_focus(outputs, focus, 5)
        rows.append(
            {
                "compressed_recall_navigation_id": stable_row_id("CRN", recall_type, source_ids(events)),
                "recall_type": recall_type,
                "focus": focus,
                "source_event_ids": source_ids(events),
                "source_event_count": len(events),
                "compressed_navigation_summary": f"{recall_type.replace('_', ' ')}: {len(events)} deterministic source events.",
                "human_review_required": True,
            }
        )
    artifact = phase43_artifact("deterministic_compressed_recall_navigation_v1")
    artifact.update({"compressed_recall_navigation_registry_id": stable_row_id("CRNREG", [row["compressed_recall_navigation_id"] for row in rows]), "compressed_recall_items": rows, "summary": {"compressed_recall_count": len(rows)}})
    return artifact


def render_compressed_recall_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("compressed_recall_navigation_registry") or {}).get("compressed_recall_items") or []
    return render_recall_page("Compressed Recall Dashboard", "compressed_recall_dashboard.html", rows, ["recall_type", "source_event_count", "compressed_navigation_summary"], "compressed_recall_navigation_id", [("Compressed recall items", len(rows))])
