"""Deterministic continuity repair review queue."""

from __future__ import annotations

from phase45_interaction_common import orphan_ids, phase45_artifact, render_interaction_page, stable_row_id


def build_continuity_repair_queue(outputs: dict) -> dict:
    rows = []
    for index, orphan_id in enumerate(orphan_ids(outputs)[:48]):
        rows.append(
            {
                "continuity_repair_queue_id": stable_row_id("CRQ", orphan_id, index),
                "orphan_id": orphan_id,
                "queue_reason": "orphaned_or_incomplete_continuity_route",
                "review_priority": index + 1,
                "repair_status": "human_review_required",
                "autonomous_repair_applied": False,
                "human_review_required": True,
            }
        )
    artifact = phase45_artifact("deterministic_continuity_repair_queue_v1")
    artifact.update({"continuity_repair_queue_id": stable_row_id("CRQREG", [row["continuity_repair_queue_id"] for row in rows]), "repair_queue_items": rows, "summary": {"continuity_repair_queue_count": len(rows)}})
    return artifact


def render_continuity_repair_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("continuity_repair_queue") or {}).get("repair_queue_items") or []
    return render_interaction_page("Continuity Repair Dashboard", "continuity_repair_dashboard.html", rows, ["orphan_id", "queue_reason", "review_priority", "repair_status", "autonomous_repair_applied"], "continuity_repair_queue_id", [("Repair queue items", len(rows))])
