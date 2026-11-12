"""Trace validated human decisions to blocker, queue, evidence, and gatekeeper artifacts."""

from __future__ import annotations

from intelligence_common import base_artifact, deterministic_id


def build_decision_provenance(validated_human_decisions: dict, decision_reconciliation: dict, tier_1_blocker_disposition: dict, compressed_review_queue: dict, review_queue: dict, reassessment_gatekeeper: dict) -> dict:
    blockers = {row.get("blocker_id"): row for row in tier_1_blocker_disposition.get("blocker_dispositions", [])}
    compressed = {row.get("compressed_item_id"): row for row in compressed_review_queue.get("compressed_items", [])}
    raw = {row.get("review_item_id"): row for row in review_queue.get("review_items", [])}
    rec_by_decision = {row.get("decision_id"): row for row in decision_reconciliation.get("reconciled_decisions") or [] if row.get("decision_id")}
    rows = []
    for decision in validated_human_decisions.get("validated_decisions") or []:
        blocker = blockers.get(decision.get("blocker_id"), {})
        compressed_item = compressed.get(blocker.get("source_compressed_item_id"), {})
        original_refs = compressed_item.get("original_item_refs") or blocker.get("original_item_refs") or []
        rows.append(
            {
                "decision_id": decision.get("decision_id"),
                "blocker_id": decision.get("blocker_id"),
                "blocker_artifact_ref": "governance/tier_1_blocker_disposition.json",
                "compressed_queue_item_ref": blocker.get("source_compressed_item_id"),
                "compressed_queue_artifact_ref": "workbench/compressed_review_queue.json",
                "original_queue_item_refs": original_refs,
                "original_queue_artifact_refs": [raw.get(ref, {}).get("artifact_path") for ref in original_refs if raw.get(ref)],
                "evidence_refs": sorted(set((decision.get("evidence_refs") or []) + (blocker.get("evidence_refs") or []))),
                "governance_threshold_ref": "governance/governance_diagnostics.json#compressed_tier_1_blockers",
                "reassessment_result_ref": "governance/reassessment_gatekeeper.json",
                "reviewer_entered_file_ref": "review_input/reviewer_decisions.json",
                "reconciliation_status": (rec_by_decision.get(decision.get("decision_id")) or {}).get("reconciliation_status"),
                "accepted_for_reassessment": (rec_by_decision.get(decision.get("decision_id")) or {}).get("accepted_for_reassessment", False),
            }
        )
    artifact = base_artifact(method="deterministic_decision_provenance_v1")
    artifact.update(
        {
            "decision_provenance_id": deterministic_id("DPROV", [(row.get("decision_id"), row.get("blocker_id"), row.get("reconciliation_status")) for row in rows]),
            "source_validated_human_decisions_ref": "governance/validated_human_decisions.json",
            "source_reassessment_gatekeeper_ref": "governance/reassessment_gatekeeper.json",
            "decision_traces": rows,
            "summary": {
                "decision_trace_count": len(rows),
                "accepted_for_reassessment_count": sum(1 for row in rows if row.get("accepted_for_reassessment")),
                "readiness_can_change": reassessment_gatekeeper.get("readiness_can_change"),
            },
        }
    )
    return artifact
