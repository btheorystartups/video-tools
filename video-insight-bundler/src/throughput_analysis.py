"""Heuristic operator throughput analysis."""

from __future__ import annotations

from operator_workflow_common import phase39_artifact, stable_row_id


def build_throughput_analysis_registry(outputs: dict) -> dict:
    specs = [
        ("review_queue", len((outputs.get("review_queue_registry") or {}).get("queue_items") or []), 18),
        ("adjudication", len((outputs.get("adjudication_queue_registry") or {}).get("queue_items") or []), 8),
        ("escalation", len((outputs.get("governance_adjudication_queue") or {}).get("queue_items") or []), 5),
        ("follow_up", len((outputs.get("imported_review_followup_queue") or {}).get("queue_items") or []), 12),
        ("packet_review", len((outputs.get("review_packet_export_registry") or {}).get("exports") or []), 6),
    ]
    rows = []
    for workflow, backlog, hourly_rate in specs:
        estimated_hours = round(backlog / hourly_rate, 3) if hourly_rate else 0
        rows.append({
            "throughput_analysis_id": stable_row_id("THRU", workflow, backlog, hourly_rate),
            "workflow": workflow,
            "backlog_items": backlog,
            "heuristic_items_per_hour": hourly_rate,
            "estimated_operator_hours": estimated_hours,
            "estimate_type": "heuristic_operational_estimate",
            "predictive_certainty_claimed": False,
        })
    artifact = phase39_artifact("deterministic_throughput_analysis_v1")
    artifact.update({"throughput_analysis_registry_id": stable_row_id("THRUREG", [row["throughput_analysis_id"] for row in rows]), "throughput_entries": rows, "summary": {"workflow_count": len(rows), "estimated_total_operator_hours": round(sum(row["estimated_operator_hours"] for row in rows), 3)}})
    return artifact
