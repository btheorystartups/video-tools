"""Release-candidate governance policy and summary generation."""

from __future__ import annotations

from intelligence_common import base_artifact, clamp, deterministic_id


DEFAULT_POLICY = {
    "minimum_corpus_size": 3,
    "minimum_validation_pass_rate": 0.95,
    "minimum_artifact_integrity": 0.92,
    "maximum_unresolved_reference_count": 0,
    "maximum_failed_video_count": 0,
    "maximum_high_severity_warning_count": 0,
    "minimum_comparative_stability": 0.6,
    "minimum_audit_completeness": 0.9,
    "minimum_provenance_coverage": 0.85,
    "maximum_mutation_risk": 0.0,
    "semantic_runtime_forbidden": True,
    "cloud_runtime_forbidden": True,
}


def build_governance_policy() -> dict:
    output = base_artifact(method="deterministic_release_candidate_governance_policy_v1")
    output.update(
        {
            "governance_policy_id": deterministic_id("GPOL", DEFAULT_POLICY),
            "policy": DEFAULT_POLICY,
            "non_mutation_policy": "No autonomous editing, semantic inference, identity recognition, cloud analysis, Resolve calls, or media/timeline mutation is permitted.",
            "summary": {"policy_rule_count": len(DEFAULT_POLICY)},
        }
    )
    return output


def build_governance_summary(policy: dict, arbitration: dict, rc_assessment: dict) -> dict:
    output = base_artifact(method="deterministic_governance_summary_v1")
    output.update(
        {
            "governance_summary_id": deterministic_id("GSUM", policy.get("governance_policy_id"), arbitration.get("classification"), rc_assessment.get("classification")),
            "classification": arbitration.get("classification"),
            "rc_assessment_classification": rc_assessment.get("classification"),
            "policy_pass_rate": (rc_assessment.get("summary") or {}).get("checklist_pass_rate"),
            "governance_readiness_score": arbitration.get("arbitrated_readiness_score"),
            "summary": {
                "classification": arbitration.get("classification"),
                "governance_readiness_score": arbitration.get("arbitrated_readiness_score"),
                "checklist_pass_rate": (rc_assessment.get("summary") or {}).get("checklist_pass_rate"),
            },
        }
    )
    return output
