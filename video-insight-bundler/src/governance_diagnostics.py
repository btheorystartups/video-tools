"""Explain conservative governance threshold decisions."""

from __future__ import annotations

from blocker_disposition import summarize_dispositions
from intelligence_common import base_artifact, clamp, deterministic_id


def _threshold(threshold_id: str, label: str, current: float, required: float, direction: str, evidence_refs: list[str], remediation: str, hard: bool = True) -> dict:
    passed = current >= required if direction == "min" else current <= required
    raw_gap = required - current if direction == "min" else current - required
    gap = round(max(0.0, raw_gap), 3)
    near = (not passed and gap <= 0.08) or (passed and abs(raw_gap) <= 0.08)
    severity = "pass" if passed else ("hard_blocker" if hard else "advisory")
    return {
        "threshold_id": threshold_id,
        "threshold_label": label,
        "current_value": round(current, 3) if isinstance(current, (int, float)) else current,
        "required_value": required,
        "gap_to_pass": gap,
        "status": "pass" if passed else "fail",
        "near_boundary": near,
        "severity": severity,
        "blocking_status": "blocking" if hard and not passed else "non_blocking",
        "evidence_refs": evidence_refs,
        "suggested_remediation": remediation,
    }


def build_governance_diagnostics(policy: dict, arbitration: dict, rc_assessment: dict, corpus_index: dict, comparative_stabilization: dict, audit_trail: dict, provenance: dict, validation_replay: dict, run_manifest: dict, compressed_review_queue: dict | None = None, blocker_analysis: dict | None = None, tier_1_blocker_disposition: dict | None = None) -> dict:
    rules = policy.get("policy") or {}
    video_count = len(corpus_index.get("videos") or [])
    validation_errors = (validation_replay.get("summary") or {}).get("missing_or_error_count") or 0
    validation_count = (validation_replay.get("summary") or {}).get("validation_count") or max(1, video_count)
    validation_pass_rate = 1.0 - min(validation_errors / max(validation_count, 1), 1.0)
    failed_videos = len(run_manifest.get("failed_videos") or [])
    disposition_summary = summarize_dispositions(tier_1_blocker_disposition, blocker_analysis)
    tier_1_count = disposition_summary.get("unresolved_tier_1_blocker_count") if tier_1_blocker_disposition else (((compressed_review_queue or {}).get("summary") or {}).get("tier_1_blocker_count") or 0)
    hard_blockers = disposition_summary.get("unresolved_hard_blocker_count") if tier_1_blocker_disposition else (((blocker_analysis or {}).get("summary") or {}).get("hard_blocker_count") or 0)
    thresholds = [
        _threshold("minimum_corpus_size", "Minimum corpus size", video_count, rules.get("minimum_corpus_size", 3), "min", ["corpus/corpus_index.json"], "Add successful analyses before promotion."),
        _threshold("validation_pass_rate", "Validation pass rate", validation_pass_rate, rules.get("minimum_validation_pass_rate", 0.95), "min", ["audit/validation_replay.json"], "Resolve validation errors and rerun validation replay."),
        _threshold("failed_video_count", "Failed video count", failed_videos, rules.get("maximum_failed_video_count", 0), "max", ["corpus/corpus_run_manifest.json"], "Rerun or exclude failed inputs only with explicit review."),
        _threshold("comparative_stability", "Comparative stability", comparative_stabilization.get("comparative_stability_score") or 0.0, rules.get("minimum_comparative_stability", 0.6), "min", ["corpus/comparative_stabilization.json"], "Review recurring destabilizers rather than lowering the stability threshold."),
        _threshold("audit_completeness", "Audit completeness", ((audit_trail.get("summary") or {}).get("audit_completeness_score") or 0.0), rules.get("minimum_audit_completeness", 0.9), "min", ["audit/audit_trail.json"], "Restore missing audit artifacts and rerun corpus analysis."),
        _threshold("provenance_coverage", "Provenance coverage", ((provenance.get("summary") or {}).get("provenance_coverage_score") or 0.0), rules.get("minimum_provenance_coverage", 0.85), "min", ["audit/provenance_reconstruction.json"], "Add traceable evidence links for readiness and recommendation decisions."),
        _threshold("compressed_tier_1_blockers", "Unresolved Tier 1 compressed blockers", tier_1_count, 0, "max", ["workbench/compressed_review_queue.json", "governance/tier_1_blocker_disposition.json"], "Review Tier 1 compressed items and document external remediation decisions.", True),
        _threshold("hard_blocker_count", "Recurring hard blocker count", hard_blockers, 0, "max", ["governance/blocker_analysis.json", "governance/hard_blocker_resolution_plan.json"], "Address recurring hard blockers before promotion.", True),
        _threshold("semantic_runtime_forbidden", "Semantic runtime remains forbidden", 0.0, 0.0, "max", ["governance/governance_policy.json"], "Keep embeddings, LLM calls, cloud APIs, and semantic runtime disabled."),
        _threshold("mutation_risk_zero", "Mutation risk remains zero", 0.0, rules.get("maximum_mutation_risk", 0.0), "max", ["governance/governance_policy.json"], "Keep all outputs review-only and non-mutating."),
    ]
    failed = [row for row in thresholds if row["status"] != "pass"]
    near = [row for row in thresholds if row.get("near_boundary")]
    diagnostics = base_artifact(method="deterministic_governance_diagnostics_v1")
    diagnostics.update(
        {
            "governance_diagnostics_id": deterministic_id("GDIAG", arbitration.get("readiness_arbitration_id"), rc_assessment.get("rc_assessment_id"), [(row["threshold_id"], row["status"], row["gap_to_pass"]) for row in thresholds]),
            "classification": arbitration.get("classification"),
            "rc_classification": rc_assessment.get("classification"),
            "not_ready_explanation": _not_ready_explanation(arbitration, failed),
            "thresholds": thresholds,
            "passed_thresholds": [row for row in thresholds if row["status"] == "pass"],
            "failed_thresholds": failed,
            "near_boundary_thresholds": near,
            "summary": {
                "threshold_count": len(thresholds),
                "failed_threshold_count": len(failed),
                "hard_blocker_count": sum(1 for row in failed if row["blocking_status"] == "blocking"),
                "near_boundary_count": len(near),
            },
        }
    )
    failure_explanations = base_artifact(method="deterministic_governance_failure_explanations_v1")
    failure_explanations.update(
        {
            "governance_failure_explanations_id": deterministic_id("GFAIL", diagnostics["governance_diagnostics_id"], [row["threshold_id"] for row in failed]),
            "classification": arbitration.get("classification"),
            "failure_explanations": [
                {
                    "threshold_id": row["threshold_id"],
                    "explanation": f"{row['threshold_label']} is {row['current_value']} with required value {row['required_value']}.",
                    "blocking_status": row["blocking_status"],
                    "gap_to_pass": row["gap_to_pass"],
                    "evidence_refs": row["evidence_refs"],
                    "suggested_remediation": row["suggested_remediation"],
                }
                for row in failed
            ],
            "summary": {"failure_count": len(failed)},
        }
    )
    return {"governance_diagnostics": diagnostics, "governance_failure_explanations": failure_explanations}


def _not_ready_explanation(arbitration: dict, failed: list[dict]) -> str:
    if arbitration.get("classification") != "not_ready":
        return "Readiness arbitration is above not_ready, but governance diagnostics remain conservative."
    blocking = [row["threshold_label"] for row in failed if row.get("blocking_status") == "blocking"]
    if not blocking:
        return "Readiness arbitration is not_ready because the arbitrated score or validation state did not clear conservative thresholds."
    return "Readiness arbitration is not_ready because hard blockers remain: " + "; ".join(blocking) + "."


def enhance_readiness_arbitration(arbitration: dict, compressed_review_queue: dict, blocker_analysis: dict, remediation_tracker: dict, governance_diagnostics: dict, rc_promotion_path: dict, tier_1_blocker_disposition: dict | None = None) -> dict:
    """Add RC-hardening context without inflating the readiness score."""

    enhanced = dict(arbitration)
    disposition_summary = summarize_dispositions(tier_1_blocker_disposition, blocker_analysis)
    hard_blockers = disposition_summary.get("unresolved_hard_blocker_count") if tier_1_blocker_disposition else ((blocker_analysis.get("summary") or {}).get("hard_blocker_count") or 0)
    tier_1 = disposition_summary.get("unresolved_tier_1_blocker_count") if tier_1_blocker_disposition else ((compressed_review_queue.get("summary") or {}).get("tier_1_blocker_count") or 0)
    failed_thresholds = (governance_diagnostics.get("summary") or {}).get("failed_threshold_count") or 0
    promotion_confidence = (rc_promotion_path.get("summary") or {}).get("promotion_confidence") or "low"
    proposed = (remediation_tracker.get("summary") or {}).get("remediation_count") or 0
    enhanced["rc_hardening_context"] = {
        "compressed_queue_severity": "tier_1_blockers_present" if tier_1 else "no_tier_1_blockers",
        "tier_1_blocker_count": tier_1,
        "hard_blocker_count": hard_blockers,
        "tier_1_disposition_artifact_ref": "governance/tier_1_blocker_disposition.json" if tier_1_blocker_disposition else None,
        "valid_non_blocking_tier_1_count": disposition_summary.get("valid_non_blocking_tier_1_count", 0) if tier_1_blocker_disposition else 0,
        "remediation_available": proposed > 0,
        "remediation_count": proposed,
        "governance_diagnostic_clarity": "clear" if failed_thresholds >= 0 else "unavailable",
        "unresolved_rc_blockers": hard_blockers + tier_1 + failed_thresholds,
        "promotion_path_confidence": promotion_confidence,
        "readiness_inflation_guard": "Remediation availability is diagnostic only and does not increase readiness.",
    }
    if hard_blockers or tier_1 or failed_thresholds:
        enhanced["classification"] = "not_ready"
        enhanced["hardening_classification_cap"] = "Unresolved RC hardening blockers prevent rc_candidate or release_candidate arbitration."
    enhanced["readiness_arbitration_id"] = deterministic_id("ARB", arbitration.get("readiness_arbitration_id"), enhanced["rc_hardening_context"])
    enhanced["summary"] = {**(arbitration.get("summary") or {}), "classification": enhanced.get("classification"), "rc_hardening_context_added": True}
    return enhanced
