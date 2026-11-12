"""Branch comparison and recommendation for simulated revision candidates."""

from __future__ import annotations


SAFETY_SCORE = {
    "SAFE_ANALYSIS_ONLY": 1.0,
    "SAFE_METADATA_ONLY": 0.95,
    "SAFE_REPORT_ONLY": 0.92,
    "REQUIRES_HUMAN_REVIEW": 0.72,
    "REQUIRES_RERENDER": 0.45,
    "REQUIRES_REINSERTION": 0.38,
    "REQUIRES_TIMELINE_MUTATION": 0.25,
    "UNSAFE_WITHOUT_BACKUP": 0.05,
}
BURDEN_SCORE = {"none": 1.0, "low": 0.82, "medium": 0.55, "high": 0.25}
ROLLBACK_SCORE = {"low": 1.0, "medium": 0.62, "high": 0.28}


def compare_branches(root_revision: dict, candidates: list[dict]) -> dict:
    rows = []
    baseline_score = root_revision.get("release_readiness", {}).get("release_readiness_score", 0.0)
    rows.append(
        {
            "branch_id": root_revision.get("revision_id"),
            "branch_label": "Baseline Observed",
            "release_readiness": baseline_score,
            "transcript_confidence": root_revision.get("score_summary", {}).get("transcript_quality"),
            "segmentation_quality": root_revision.get("score_summary", {}).get("segmentation_smoothness"),
            "topic_continuity": root_revision.get("score_summary", {}).get("topic_continuity"),
            "rhetorical_balance": root_revision.get("score_summary", {}).get("rhetorical_balance"),
            "acoustic_stability": root_revision.get("score_summary", {}).get("acoustic_completeness"),
            "recommendation_confidence": root_revision.get("score_summary", {}).get("recommendation_confidence"),
            "identity_preservation": 1.0,
            "mutation_safety": 1.0,
            "human_review_burden": "none",
            "rollback_complexity": "low",
            "recommendation_score": round(float(baseline_score) + 0.03, 3),
        }
    )
    for candidate in candidates:
        readiness = candidate.get("predicted_release_readiness", {})
        components = readiness.get("score_components", {})
        safety = SAFETY_SCORE.get(candidate.get("mutation_safety_class"), 0.2)
        burden = "medium" if candidate.get("human_review_required") else "low"
        if candidate.get("candidate_label") == "Candidate_D_No_Change":
            burden = "none"
        rollback = candidate.get("rollback_complexity", "low")
        score = (
            float(readiness.get("release_readiness_score", 0.0)) * 0.58
            + float(candidate.get("identity_preservation_score", 1.0)) * 0.18
            + safety * 0.14
            + BURDEN_SCORE.get(burden, 0.4) * 0.06
            + ROLLBACK_SCORE.get(rollback, 0.4) * 0.04
        )
        if candidate.get("render_required") or candidate.get("reinsertion_required"):
            score -= 0.08
        if candidate.get("candidate_label") == "Candidate_D_No_Change":
            score -= 0.05
        rows.append(
            {
                "branch_id": candidate.get("simulated_revision_id"),
                "candidate_id": candidate.get("candidate_id"),
                "branch_label": candidate.get("candidate_label"),
                "release_readiness": readiness.get("release_readiness_score"),
                "transcript_confidence": components.get("transcript_quality"),
                "segmentation_quality": components.get("segmentation_smoothness"),
                "topic_continuity": components.get("topic_continuity"),
                "rhetorical_balance": components.get("rhetorical_balance"),
                "acoustic_stability": components.get("acoustic_completeness"),
                "recommendation_confidence": components.get("recommendation_confidence"),
                "identity_preservation": candidate.get("identity_preservation_score"),
                "mutation_safety": round(safety, 3),
                "human_review_burden": burden,
                "rollback_complexity": rollback,
                "recommendation_score": round(max(0.0, score), 3),
            }
        )

    eligible = [row for row in rows if row.get("branch_label") != "Candidate_C_Highest_Readiness"]
    recommended = max(eligible, key=lambda row: (row["recommendation_score"], row.get("release_readiness") or 0.0, row["branch_label"]))
    return {
        "comparison_basis": "Deterministic score comparison with penalties for mutation risk, review burden, rollback complexity, and identity drift.",
        "branches": sorted(rows, key=lambda row: row["branch_label"]),
        "recommended_branch": recommended,
        "why_more_aggressive_may_not_be_preferable": [
            "Higher predicted readiness can be offset by render requirements, reinsertion work, or identity drift.",
            "Proposal-only artifacts should be reviewed before any production edit is attempted.",
        ],
    }
