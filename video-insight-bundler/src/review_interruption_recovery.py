"""Interruption recovery summaries for operator review sessions."""

from __future__ import annotations

from operator_workflow_common import ergonomics_links, phase40_artifact, render_registry_page, stable_row_id


def build_interruption_recovery_registry(outputs: dict) -> dict:
    specs = [
        ("suggested_resume_point", _first(outputs, "session_focus_restore_registry", "focus_restore_entries", "focus_restore_id"), "Continue from the most recent deterministic focus marker."),
        ("interrupted_review_summary", _summary_ref(outputs), "Review open queue, follow-up, and escalation counts before resuming."),
        ("unresolved_high_priority_queue", _first(outputs, "high_priority_review_queue", "queue_items", "queue_item_id"), "Resume the highest-priority queue visible in the local artifacts."),
        ("unfinished_adjudication_summary", _first(outputs, "adjudication_queue_registry", "queue_items", "queue_item_id"), "Review unfinished adjudication context without applying a resolution."),
    ]
    rows = [{"interruption_recovery_id": stable_row_id("IREC", kind, ref), "recovery_type": kind, "target_ref": ref or "unavailable", "resume_guidance": guidance, "autonomous_resume_performed": False, "requires_human_review": True} for kind, ref, guidance in specs]
    artifact = phase40_artifact("deterministic_review_interruption_recovery_v1")
    artifact.update({"interruption_recovery_registry_id": stable_row_id("IRECREG", [row["interruption_recovery_id"] for row in rows]), "recovery_entries": rows, "summary": {"recovery_entry_count": len(rows)}})
    return artifact


def render_interruption_recovery_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("interruption_recovery_registry") or {}).get("recovery_entries") or []
    return {"interruption_recovery_dashboard.html": render_registry_page("Interruption Recovery Dashboard", "Session Ergonomics", "interruption_recovery_dashboard.html", rows, ["recovery_type", "target_ref", "resume_guidance", "autonomous_resume_performed"], "interruption_recovery_id", [("Recovery entries", len(rows))], ergonomics_links(""))}


def _first(outputs: dict, key: str, field: str, id_field: str) -> str | None:
    row = (((outputs.get(key) or {}).get(field) or [{}])[0])
    return row.get(id_field) or row.get("item_id")


def _summary_ref(outputs: dict) -> str:
    return stable_row_id("ISUM", len((outputs.get("review_queue_registry") or {}).get("queue_items") or []), len((outputs.get("review_followup_registry") or {}).get("followup_items") or []), len((outputs.get("review_escalation_registry") or {}).get("escalation_items") or []))
