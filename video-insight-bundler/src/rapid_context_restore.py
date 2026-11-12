"""Deterministic rapid context restoration."""

from __future__ import annotations

from phase43_recall_common import events_for_focus, phase43_artifact, render_recall_page, source_ids, stable_row_id


def build_rapid_context_restore_registry(outputs: dict) -> dict:
    specs = [
        ("where_you_left_off", "handoff"),
        ("major_changes_since_last_review", "throughput"),
        ("highest_priority_unresolved_changes", "governance"),
        ("largest_governance_shifts", "governance"),
        ("largest_operational_regressions", "workload"),
    ]
    rows = []
    for restore_type, focus in specs:
        events = events_for_focus(outputs, focus, 4)
        rows.append(
            {
                "rapid_context_restore_id": stable_row_id("RCR", restore_type, source_ids(events)),
                "restore_type": restore_type,
                "focus": focus,
                "source_event_ids": source_ids(events),
                "source_event_count": len(events),
                "restore_summary": f"{restore_type.replace('_', ' ')} can be restored from {len(events)} linked deterministic events.",
                "human_review_required": True,
            }
        )
    artifact = phase43_artifact("deterministic_rapid_context_restore_v1")
    artifact.update({"rapid_context_restore_registry_id": stable_row_id("RCRREG", [row["rapid_context_restore_id"] for row in rows]), "restore_items": rows, "summary": {"rapid_context_restore_count": len(rows)}})
    return artifact


def render_rapid_context_restore_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("rapid_context_restore_registry") or {}).get("restore_items") or []
    return render_recall_page("Rapid Context Restore Dashboard", "rapid_context_restore_dashboard.html", rows, ["restore_type", "source_event_count", "restore_summary"], "rapid_context_restore_id", [("Restore items", len(rows))])
