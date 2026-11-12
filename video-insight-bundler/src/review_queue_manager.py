"""Operational review queue generation."""

from __future__ import annotations

from review_operational_common import priority_score, review_artifact
from stability import deterministic_id


def _queue_item(queue_type: str, related: str | None, severity: str, effort: str, recs: list[str], annotations: list[str], segments: list[str], gov: list[str], action: str) -> dict:
    score = priority_score(severity, effort, 0.8 if queue_type in {"governance_critical", "escalation_required", "unresolved_blockers"} else 0.6)
    return {"queue_id": deterministic_id("RQ", queue_type, related, severity, effort), "queue_type": queue_type, "related_artifact": related, "severity": severity, "effort_estimate": effort, "expected_review_time": "5-12 minutes" if effort == "low effort" else "12-25 minutes", "related_recommendations": recs, "related_annotations": annotations, "related_segments": segments, "related_governance_items": gov, "suggested_next_action": action, "review_priority_score": score}


def build_review_queue_artifacts(outputs: dict, annotations: dict, followups: dict, escalations: dict) -> dict:
    items = []
    for rec in (outputs.get("recommendation_traceability") or {}).get("traceability_entries") or []:
        severity = rec.get("severity") or "review"
        effort = rec.get("effort_estimate") or "medium effort"
        qtype = "lowest_effort_highest_impact" if "low" in effort.lower() else "highest_severity_first" if severity == "high" else "review_completion_pending"
        items.append(_queue_item(qtype, rec.get("recommendation_id"), severity, effort, [rec.get("recommendation_id")], [], [rec.get("affected_segment")], [], rec.get("recommended_next_action") or "Review recommendation evidence."))
    for ann in annotations.get("annotations") or []:
        if ann.get("annotation_type") == "followup_note":
            items.append(_queue_item("follow-up_required", ann.get("annotation_id"), ann.get("severity"), "medium effort", [ann.get("related_recommendation")], [ann.get("annotation_id")], [ann.get("related_segment")], [ann.get("related_blocker")], "Resolve or defer the follow-up note with reviewer rationale."))
    for esc in escalations.get("escalation_items") or []:
        items.append(_queue_item("escalation_required", esc.get("escalation_id"), esc.get("severity"), "medium effort", [], [], [], [esc.get("related_artifact")], esc.get("suggested_reviewer_action")))
    for blocker in (outputs.get("tier_1_blocker_disposition") or {}).get("blocker_dispositions") or []:
        items.append(_queue_item("unresolved_blockers", blocker.get("blocker_id"), "high", "medium effort", [], [], [], [blocker.get("blocker_id")], "Review blocker disposition and capture human decision evidence."))
    registry = review_artifact("deterministic_review_queue_registry_v1")
    items = sorted(items, key=lambda row: (-row["review_priority_score"], row["queue_type"], row["queue_id"]))
    registry.update({"review_queue_registry_id": deterministic_id("RQREG", [row["queue_id"] for row in items]), "queue_items": items, "summary": {"queue_item_count": len(items), "escalation_required_count": sum(1 for row in items if row["queue_type"] == "escalation_required")}})
    outputs_by_key = {"review_queue_registry": registry}
    queue_specs = [
        ("high_priority_review_queue", lambda r: r["severity"] == "high" or r["review_priority_score"] >= 0.75),
        ("low_effort_high_impact_queue", lambda r: r["queue_type"] == "lowest_effort_highest_impact"),
        ("unresolved_blocker_queue", lambda r: r["queue_type"] == "unresolved_blockers"),
        ("escalation_required_queue", lambda r: r["queue_type"] == "escalation_required"),
        ("governance_review_queue", lambda r: r["queue_type"] in {"governance_critical", "unresolved_blockers", "escalation_required"}),
        ("pacing_review_queue", lambda r: "pacing" in str(r["related_artifact"]).lower() or "pacing" in str(r["suggested_next_action"]).lower()),
        ("rhetorical_review_queue", lambda r: "claim" in str(r["related_artifact"]).lower() or "rhetorical" in str(r["suggested_next_action"]).lower()),
    ]
    for key, pred in queue_specs:
        rows = [row for row in items if pred(row)]
        artifact = review_artifact(f"deterministic_{key}_v1")
        artifact.update({f"{key}_id": deterministic_id("RQSUB", key, [row["queue_id"] for row in rows]), "queue_items": rows, "summary": {"queue_item_count": len(rows)}})
        outputs_by_key[key] = artifact
    return outputs_by_key
