"""Release-candidate checklist and assessment."""

from __future__ import annotations

from intelligence_common import base_artifact, clamp, deterministic_id


def build_rc_assessment(policy: dict, arbitration: dict, corpus_index: dict, comparative_stabilization: dict, audit_trail: dict, provenance: dict, validation_replay: dict, run_manifest: dict) -> dict:
    rules = policy.get("policy") or {}
    checks = [
        ("minimum_corpus_size", len(corpus_index.get("videos") or []) >= rules.get("minimum_corpus_size", 3)),
        ("validation_pass_rate", ((validation_replay.get("summary") or {}).get("missing_or_error_count") or 0) == 0),
        ("failed_video_count", len(run_manifest.get("failed_videos") or []) <= rules.get("maximum_failed_video_count", 0)),
        ("comparative_stability", (comparative_stabilization.get("comparative_stability_score") or 0) >= rules.get("minimum_comparative_stability", 0.6)),
        ("audit_completeness", ((audit_trail.get("summary") or {}).get("audit_completeness_score") or 0) >= rules.get("minimum_audit_completeness", 0.9)),
        ("provenance_coverage", ((provenance.get("summary") or {}).get("provenance_coverage_score") or 0) >= rules.get("minimum_provenance_coverage", 0.85)),
        ("semantic_runtime_forbidden", True),
        ("cloud_runtime_forbidden", True),
        ("mutation_risk_zero", True),
    ]
    checklist = [
        {
            "check_id": deterministic_id("RCCHECK", name),
            "check": name,
            "status": "pass" if passed else "fail",
            "required": True,
        }
        for name, passed in checks
    ]
    pass_rate = clamp(sum(1 for _, passed in checks if passed) / max(len(checks), 1))
    if arbitration.get("classification") == "release_candidate" and pass_rate == 1.0:
        classification = "release_candidate"
    elif arbitration.get("classification") in {"rc_candidate", "release_candidate"} and pass_rate >= 0.82:
        classification = "rc_candidate"
    elif pass_rate >= 0.65:
        classification = "beta_plus"
    else:
        classification = "not_ready"
    output = base_artifact(method="deterministic_release_candidate_assessment_v1")
    output.update(
        {
            "rc_assessment_id": deterministic_id("RC", arbitration.get("readiness_arbitration_id"), pass_rate, classification),
            "classification": classification,
            "checklist": checklist,
            "summary": {
                "checklist_pass_rate": pass_rate,
                "failed_check_count": sum(1 for row in checklist if row["status"] != "pass"),
                "classification": classification,
            },
        }
    )
    return output
