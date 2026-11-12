"""Conservative corpus readiness arbitration."""

from __future__ import annotations

from intelligence_common import avg, base_artifact, clamp, deterministic_id


def _classify(score: float, failed: int, stability: str, validation_ok: bool) -> str:
    if failed or not validation_ok or score < 0.55:
        return "not_ready"
    if score < 0.68 or stability in {"insufficient_corpus", "unstable"}:
        return "beta_plus"
    if score < 0.82 or stability == "emerging":
        return "rc_candidate"
    return "release_candidate"


def build_readiness_arbitration(corpus_index: dict, corpus_intelligence: dict, comparative_stabilization: dict, audit_trail: dict, validation_replay: dict, policy: dict, run_manifest: dict) -> dict:
    policy_rules = policy.get("policy", {})
    per_video_scores = [row.get("readiness_score") for row in corpus_index.get("videos", [])]
    per_video_readiness = avg(per_video_scores)
    corpus_readiness = corpus_intelligence.get("corpus_level_confidence") or 0.0
    comparative_readiness = comparative_stabilization.get("comparative_stability_score") or 0.0
    audit_readiness = (audit_trail.get("summary") or {}).get("audit_completeness_score") or 0.0
    validation_errors = (validation_replay.get("summary") or {}).get("missing_or_error_count") or 0
    validation_readiness = 1.0 if validation_errors == 0 else 0.4
    failed = len(run_manifest.get("failed_videos") or [])
    failed_penalty = clamp(1.0 - failed / max(len(corpus_index.get("videos") or []), 1))
    score = avg([per_video_readiness, corpus_readiness, comparative_readiness, audit_readiness, validation_readiness, failed_penalty])
    validation_ok = validation_errors == 0 and failed <= policy_rules.get("maximum_failed_video_count", 0)
    classification = _classify(score, failed, comparative_stabilization.get("classification"), validation_ok)
    output = base_artifact(method="deterministic_readiness_arbitration_v1")
    output.update(
        {
            "readiness_arbitration_id": deterministic_id("ARB", score, failed, comparative_stabilization.get("classification")),
            "per_video_readiness": per_video_readiness,
            "corpus_readiness": corpus_readiness,
            "integrity_readiness": validation_readiness,
            "comparative_readiness": comparative_readiness,
            "audit_readiness": audit_readiness,
            "governance_readiness": failed_penalty,
            "arbitrated_readiness_score": score,
            "classification": classification,
            "decision_factors": {
                "failed_video_count": failed,
                "validation_error_count": validation_errors,
                "comparative_stability_classification": comparative_stabilization.get("classification"),
                "minimum_corpus_size_met": len(corpus_index.get("videos") or []) >= policy_rules.get("minimum_corpus_size", 3),
            },
            "summary": {"classification": classification, "arbitrated_readiness_score": score},
        }
    )
    return output
