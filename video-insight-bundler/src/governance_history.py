"""Deterministic governance history snapshots and replay logs."""

from __future__ import annotations

from intelligence_common import base_artifact, deterministic_id


def build_governance_history(readiness_arbitration: dict, rc_assessment: dict, governance_reassessment: dict, governance_review_session: dict, tier_1_blocker_disposition: dict) -> dict:
    snapshot = {
        "snapshot_id": deterministic_id("GSNAP", readiness_arbitration.get("readiness_arbitration_id"), rc_assessment.get("rc_assessment_id"), governance_reassessment.get("governance_reassessment_id"), governance_review_session.get("session_id")),
        "readiness_classification": readiness_arbitration.get("classification"),
        "readiness_score": readiness_arbitration.get("arbitrated_readiness_score"),
        "rc_classification": rc_assessment.get("classification"),
        "reassessment_id": governance_reassessment.get("governance_reassessment_id"),
        "review_session_id": governance_review_session.get("session_id"),
        "tier_1_blocker_disposition_id": tier_1_blocker_disposition.get("tier_1_blocker_disposition_id"),
        "blocker_disposition_summary": tier_1_blocker_disposition.get("summary") or {},
    }
    history = base_artifact(method="deterministic_governance_history_v1")
    history.update(
        {
            "governance_history_id": deterministic_id("GHIST", snapshot),
            "governance_state_changes": [_state_change(snapshot)],
            "readiness_changes": [
                {
                    "snapshot_id": snapshot["snapshot_id"],
                    "classification": snapshot["readiness_classification"],
                    "score": snapshot["readiness_score"],
                }
            ],
            "reassessment_runs": [governance_reassessment.get("governance_reassessment_id")],
            "blocker_disposition_changes": [
                {
                    "blocker_id": row.get("blocker_id"),
                    "disposition": row.get("disposition"),
                    "decision_evidence_refs": row.get("decision_evidence_refs") or [],
                }
                for row in tier_1_blocker_disposition.get("blocker_dispositions", [])
            ],
            "classification_history": [snapshot["readiness_classification"]],
            "rc_promotion_attempts": [{"classification": snapshot["rc_classification"], "allowed": snapshot["readiness_classification"] in {"rc_candidate", "release_candidate"}}],
            "reviewer_sessions": [governance_review_session.get("session_id")],
            "snapshots": [snapshot],
            "summary": {"snapshot_count": 1, "reviewer_session_count": 1, "reassessment_run_count": 1},
        }
    )
    registry = base_artifact(method="deterministic_governance_snapshot_registry_v1")
    registry.update({"governance_snapshot_registry_id": deterministic_id("GSNAPREG", snapshot["snapshot_id"]), "snapshots": [{"snapshot_id": snapshot["snapshot_id"], "history_ref": "governance/governance_history.json"}], "summary": {"snapshot_count": 1}})
    replay = base_artifact(method="deterministic_governance_replay_log_v1")
    replay.update(
        {
            "governance_replay_log_id": deterministic_id("GREPLAY", snapshot["snapshot_id"]),
            "replay_steps": [
                {"step": 1, "artifact_ref": "governance/tier_1_blocker_disposition.json", "action": "load blocker dispositions"},
                {"step": 2, "artifact_ref": "governance/governance_review_session.json", "action": "capture reviewer session snapshot"},
                {"step": 3, "artifact_ref": "governance/governance_reassessment.json", "action": "run deterministic reassessment"},
                {"step": 4, "artifact_ref": "governance/governance_reassessment_delta.json", "action": "explain readiness delta"},
            ],
            "summary": {"replay_step_count": 4},
        }
    )
    return {"governance_history": history, "governance_snapshot_registry": registry, "governance_replay_log": replay}


def _state_change(snapshot: dict) -> dict:
    return {
        "snapshot_id": snapshot["snapshot_id"],
        "state": snapshot["readiness_classification"],
        "reason": "Governance snapshot captured after deterministic reassessment.",
        "evidence_refs": ["governance/readiness_arbitration.json", "governance/governance_reassessment.json"],
    }
