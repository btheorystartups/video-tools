"""Session focus restoration registry."""

from __future__ import annotations

from operator_workflow_common import phase40_artifact, stable_row_id


def build_session_focus_restore_registry(outputs: dict) -> dict:
    session = ((outputs.get("review_session_registry") or {}).get("sessions") or [{}])[0]
    checkpoint = ((outputs.get("review_checkpoints") or {}).get("checkpoints") or [{}])[0]
    ambiguity = ((outputs.get("unresolved_ambiguity_registry") or {}).get("ambiguities") or [{}])[0]
    entries = [
        ("last_review_position", checkpoint.get("current_segment") or session.get("last_reviewed_segment"), checkpoint.get("current_page") or session.get("last_opened_timeline")),
        ("last_viewed_evidence", ambiguity.get("evidence_ref") or ambiguity.get("ambiguity_id"), "visualizations/adjudication/unresolved_ambiguity_dashboard.html"),
        ("last_active_queue", _first_queue_ref(outputs), "visualizations/review/review_queue_dashboard.html"),
        ("last_adjudication_context", _first_ref(outputs, "adjudication_queue_registry"), "visualizations/adjudication/adjudication_queue_dashboard.html"),
        ("last_unresolved_ambiguity_focus", ambiguity.get("ambiguity_id"), "visualizations/adjudication/unresolved_ambiguity_dashboard.html"),
    ]
    rows = [{"focus_restore_id": stable_row_id("SFOC", kind, ref), "focus_type": kind, "target_ref": ref or "unavailable", "restore_href": href, "requires_human_review": True, "hidden_runtime_state_used": False} for kind, ref, href in entries]
    artifact = phase40_artifact("deterministic_session_focus_restore_v1")
    artifact.update({"session_focus_restore_registry_id": stable_row_id("SFOCREG", [row["focus_restore_id"] for row in rows]), "focus_restore_entries": rows, "summary": {"focus_restore_entry_count": len(rows)}})
    return artifact


def _first_queue_ref(outputs: dict) -> str | None:
    for key in ["review_queue_registry", "high_priority_review_queue", "adjudication_queue_registry"]:
        ref = _first_ref(outputs, key)
        if ref:
            return ref
    return None


def _first_ref(outputs: dict, key: str) -> str | None:
    row = (((outputs.get(key) or {}).get("queue_items") or [{}])[0])
    return row.get("queue_item_id") or row.get("item_id") or row.get("queue_id")
