"""Deterministic reviewer annotation scaffolding and indexes."""

from __future__ import annotations

from review_operational_common import REVIEW_LIMITATION, count_by, review_artifact, stable_timestamp
from stability import deterministic_id


ANNOTATION_TYPES = [
    "segment_annotation",
    "recommendation_annotation",
    "blocker_annotation",
    "evidence_annotation",
    "governance_annotation",
    "optimization_rationale",
    "review_comment",
    "followup_note",
    "escalation_note",
    "accepted_risk_rationale",
    "preserve_as_intentional_rationale",
]


def _base_annotation(annotation_type: str, related_video: str | None, related_segment: str | None, related_recommendation: str | None, related_blocker: str | None, severity: str, text: str, refs: list[str], journey: str | None = None) -> dict:
    annotation_id = deterministic_id("ANN", annotation_type, related_video, related_segment, related_recommendation, related_blocker, text)
    escalation = annotation_type == "escalation_note" or severity in {"critical", "high"} and annotation_type in {"blocker_annotation", "governance_annotation"}
    followup = annotation_type in {"followup_note", "accepted_risk_rationale", "preserve_as_intentional_rationale"} or escalation
    return {
        "annotation_id": annotation_id,
        "reviewer_id": "local_reviewer_placeholder",
        "timestamp": stable_timestamp(annotation_id),
        "related_video": related_video,
        "related_segment": related_segment,
        "related_recommendation": related_recommendation,
        "related_blocker": related_blocker,
        "annotation_type": annotation_type,
        "annotation_text": text,
        "severity": severity or "review",
        "review_status": "open_review",
        "followup_required": bool(followup),
        "escalation_required": bool(escalation),
        "evidence_refs": refs,
        "related_artifacts": refs,
        "related_review_journey": journey,
        "related_checkpoint": None,
        "non_claim_limitation": REVIEW_LIMITATION,
    }


def build_reviewer_annotation_artifacts(outputs: dict) -> dict:
    temporal = (outputs.get("temporal_evidence_index") or {}).get("temporal_evidence_entries") or []
    recs = (outputs.get("recommendation_traceability") or {}).get("traceability_entries") or []
    blockers = (outputs.get("tier_1_blocker_disposition") or {}).get("blocker_dispositions") or []
    annotations: list[dict] = []
    for entry in temporal[:40]:
        severity = ((entry.get("highest_severity_signal") or {}).get("severity") or entry.get("severity") or "review")
        annotations.append(_base_annotation("segment_annotation", entry.get("video_id"), entry.get("segment_id"), None, None, severity, "Review note placeholder for this timeline segment; human rationale can be added locally without mutating media.", ["timeline/temporal_evidence_index.json"], "timeline_segment_review"))
        if severity == "high":
            annotations.append(_base_annotation("followup_note", entry.get("video_id"), entry.get("segment_id"), None, None, severity, "Follow-up candidate: revisit this high-severity timeline review signal after human review.", ["timeline/temporal_evidence_index.json"], "followup_review"))
    for rec in recs[:40]:
        annotations.append(_base_annotation("recommendation_annotation", rec.get("video_id") or rec.get("source_video"), rec.get("affected_segment"), rec.get("recommendation_id"), None, rec.get("severity") or "review", "Recommendation review note placeholder; reviewer should record accept, defer, reject, or preserve-as-intentional rationale.", ["recommendations/recommendation_traceability.json"], "recommendation_review"))
        if rec.get("severity") == "high":
            annotations.append(_base_annotation("escalation_note", rec.get("video_id") or rec.get("source_video"), rec.get("affected_segment"), rec.get("recommendation_id"), None, "high", "Escalation candidate because this recommendation carries high review priority.", ["recommendations/recommendation_traceability.json"], "escalation_review"))
    for blocker in blockers[:40]:
        annotations.append(_base_annotation("blocker_annotation", None, None, None, blocker.get("blocker_id"), "high", "Blocker review note placeholder; do not auto-resolve without explicit human decision evidence.", ["governance/tier_1_blocker_disposition.json"], "governance_blocker_review"))
    if recs:
        rec = recs[0]
        annotations.append(_base_annotation("accepted_risk_rationale", rec.get("video_id") or rec.get("source_video"), rec.get("affected_segment"), rec.get("recommendation_id"), None, rec.get("severity") or "review", "Accepted-risk rationale placeholder for preserving an issue as intentional only after human review.", ["recommendations/recommendation_lineage.json"], "risk_acceptance_review"))
        annotations.append(_base_annotation("preserve_as_intentional_rationale", rec.get("video_id") or rec.get("source_video"), rec.get("affected_segment"), rec.get("recommendation_id"), None, "medium", "Preserve-as-intentional rationale placeholder; requires reviewer explanation and evidence reference.", ["recommendations/recommendation_traceability.json"], "style_intent_review"))
    registry = review_artifact("deterministic_reviewer_annotations_v1")
    registry.update({"reviewer_annotations_id": deterministic_id("ANNREG", [row["annotation_id"] for row in annotations]), "annotations": annotations, "summary": {"annotation_count": len(annotations), "followup_required_count": sum(1 for row in annotations if row["followup_required"]), "escalation_required_count": sum(1 for row in annotations if row["escalation_required"])}})
    groups = review_artifact("deterministic_annotation_group_registry_v1")
    groups.update({"annotation_group_registry_id": deterministic_id("ANGRP", registry["reviewer_annotations_id"]), "groups": [{"group_id": deterministic_id("ANG", key), "annotation_type": key, "annotation_count": value} for key, value in sorted(count_by(annotations, "annotation_type").items())], "summary": {"group_count": len(count_by(annotations, "annotation_type"))}})
    filters = review_artifact("deterministic_annotation_filter_registry_v1")
    filters.update({"annotation_filter_registry_id": deterministic_id("ANFLT", registry["reviewer_annotations_id"]), "filters": [{"filter_id": "followup_required", "label": "Follow-up required", "matching_annotation_ids": [row["annotation_id"] for row in annotations if row["followup_required"]]}, {"filter_id": "escalation_required", "label": "Escalation required", "matching_annotation_ids": [row["annotation_id"] for row in annotations if row["escalation_required"]]}, {"filter_id": "governance", "label": "Governance annotations", "matching_annotation_ids": [row["annotation_id"] for row in annotations if "governance" in row["annotation_type"] or row["related_blocker"]]}], "summary": {"filter_count": 3}})
    review_index = review_artifact("deterministic_annotation_review_index_v1")
    review_index.update({"annotation_review_index_id": deterministic_id("ANIDX", registry["reviewer_annotations_id"]), "annotation_review_items": [{"annotation_id": row["annotation_id"], "review_status": row["review_status"], "followup_required": row["followup_required"], "escalation_required": row["escalation_required"], "related_review_journey": row["related_review_journey"]} for row in annotations], "summary": {"review_item_count": len(annotations)}})
    crosslinks = review_artifact("deterministic_annotation_crosslinks_v1")
    crosslinks.update({"annotation_crosslinks_id": deterministic_id("ANX", registry["reviewer_annotations_id"]), "crosslinks": [{"annotation_id": row["annotation_id"], "target_path": "visualizations/review/reviewer_annotations.html", "related_segment": row["related_segment"], "related_recommendation": row["related_recommendation"], "related_blocker": row["related_blocker"], "evidence_refs": row["evidence_refs"]} for row in annotations], "summary": {"crosslink_count": len(annotations)}})
    return {"reviewer_annotations": registry, "annotation_group_registry": groups, "annotation_filter_registry": filters, "annotation_review_index": review_index, "annotation_crosslinks": crosslinks}
