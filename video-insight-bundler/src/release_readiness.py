"""Conservative deterministic release readiness scoring."""

from __future__ import annotations

from statistics import mean


DEFAULT_WEIGHTS = {
    "transcript_quality": 0.16,
    "segmentation_smoothness": 0.12,
    "acoustic_completeness": 0.1,
    "topic_continuity": 0.11,
    "rhetorical_balance": 0.11,
    "recommendation_confidence": 0.12,
    "warning_severity": 0.09,
    "constraint_pass_rate": 0.09,
    "mutation_safety": 0.05,
    "identity_preservation": 0.05,
    "modality_agreement_quality": 0.08,
    "segmentation_confidence": 0.08,
    "evidence_stability": 0.07,
    "revision_evidence_quality": 0.05,
    "rhetorical_coherence_score": 0.08,
    "boundary_diagnostic_quality": 0.07,
    "unsupported_shift_penalty": 0.06,
    "unresolved_question_penalty": 0.05,
    "claim_without_example_penalty": 0.04,
    "discourse_continuity": 0.08,
    "argument_completeness": 0.08,
    "callback_resolution_quality": 0.07,
    "narrative_persistence": 0.06,
    "ambiguity_adjusted_continuity": 0.07,
    "unresolved_discourse_pressure": 0.06,
    "contradiction_cluster_pressure": 0.05,
    "visual_continuity_quality": 0.07,
    "visual_boundary_alignment_quality": 0.07,
    "visual_evidence_completeness": 0.06,
    "visual_contradiction_pressure": 0.06,
    "visual_reset_support": 0.04,
    "structural_coherence": 0.06,
    "temporal_rhythm_stability": 0.05,
    "editorial_pressure": 0.06,
    "recommendation_dependency_pressure": 0.05,
    "revision_propagation_risk": 0.05,
    "counterfactual_uncertainty": 0.04,
    "epistemic_stability": 0.05,
    "creator_stability": 0.04,
    "comparative_volatility": 0.04,
    "recurring_structural_debt": 0.04,
}


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def _num(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _status_score(status: str | None) -> float:
    return {
        "complete": 1.0,
        "limited": 0.65,
        "skipped": 0.35,
        "unavailable": 0.25,
        "error": 0.1,
    }.get(status or "", 0.35)


def _warning_score(warnings: list[dict]) -> float:
    penalty = 0.0
    for item in warnings:
        penalty += {"error": 0.22, "warning": 0.08, "info": 0.025}.get(item.get("severity"), 0.06)
    return _clamp(1.0 - min(0.65, penalty))


def release_class(score: float, blocking_issues: list[str]) -> str:
    if blocking_issues or score < 0.5:
        return "not_ready"
    if score < 0.68:
        return "review_ready"
    if score < 0.82:
        return "dry_run_ready"
    return "release_candidate"


def compute_release_readiness(
    bundle,
    report_data: dict,
    constraint_report: dict,
    revision_profile: dict | None = None,
    *,
    mutation_safety_score: float = 1.0,
    identity_preservation_score: float = 1.0,
    candidate_adjustments: dict | None = None,
) -> dict:
    weights = dict(DEFAULT_WEIGHTS)
    weights.update((revision_profile or {}).get("release_readiness_weights") or {})
    quality = report_data.get("quality_scores", {})
    topic = getattr(bundle, "topic_analysis", None) or {}
    rhetoric = getattr(bundle, "rhetorical_analysis", None) or {}
    topic_continuity = getattr(bundle, "topic_continuity", None) or {}
    rhetorical_coherence = getattr(bundle, "rhetorical_coherence", None) or {}
    boundary_diagnostics = getattr(bundle, "boundary_diagnostics", None) or {}
    discourse_state = getattr(bundle, "discourse_state", None) or {}
    argument_graph = getattr(bundle, "argument_graph", None) or {}
    narrative_memory = getattr(bundle, "narrative_memory", None) or {}
    callback_resolution = getattr(bundle, "callback_resolution", None) or {}
    discourse_summary = getattr(bundle, "discourse_summary", None) or {}
    acoustic = getattr(bundle, "acoustic_features", None) or {}
    consensus_outputs = getattr(bundle, "consensus_outputs", None) or {}
    visual_structure = getattr(bundle, "visual_structure", None) or {}
    visual_continuity = getattr(bundle, "visual_continuity", None) or {}
    visual_alignment = getattr(bundle, "visual_boundary_alignment", None) or {}
    sequence_outputs = getattr(bundle, "sequence_outputs", None) or {}
    comparative_outputs = getattr(bundle, "comparative_outputs", None) or {}
    sequence_summary = sequence_outputs.get("sequence_summary") or {}
    comparative_summary = comparative_outputs.get("comparative_summary") or {}
    consensus = consensus_outputs.get("evidence_consensus") or {}
    transition = consensus_outputs.get("transition_confidence") or {}
    modality_agreement = consensus_outputs.get("modality_agreement") or {}
    evidence_scores = consensus_outputs.get("evidence_score_summary") or {}
    false_positive = consensus_outputs.get("false_positive_boundaries") or {}
    constraints = constraint_report.get("summary", {})
    candidate_adjustments = candidate_adjustments or {}
    transition_confidence_mean = _num(((transition.get("summary", {}) or {}).get("confidence_distribution", {}) or {}).get("mean"), quality.get("segmentation_smoothness", 0.35))
    consensus_mean = _num(((consensus.get("summary", {}) or {}).get("consensus_score_distribution", {}) or {}).get("mean"), 0.45)
    modality_agreement_mean = _num((modality_agreement.get("summary", {}) or {}).get("mean_agreement_score"), 0.5)
    evidence_strength = _num(evidence_scores.get("overall_evidence_strength"), 0.45)

    metrics = {
        "transcript_quality": _clamp(quality.get("transcript_quality", 0.35) + candidate_adjustments.get("transcript_quality", 0.0)),
        "segmentation_smoothness": _clamp(quality.get("segmentation_smoothness", 0.35) + candidate_adjustments.get("segmentation_smoothness", 0.0)),
        "acoustic_completeness": _clamp(_status_score(acoustic.get("analysis_status")) + candidate_adjustments.get("acoustic_completeness", 0.0)),
        "topic_continuity": _clamp(topic_continuity.get("topic_continuity_score", 1.0 - float(topic.get("topic_drift_score") if topic.get("topic_drift_score") is not None else 0.6)) + candidate_adjustments.get("topic_continuity", 0.0)),
        "rhetorical_balance": _clamp((rhetoric.get("rhetorical_balance_score") if rhetoric.get("rhetorical_balance_score") is not None else quality.get("rhetorical_consistency", 0.35)) + candidate_adjustments.get("rhetorical_balance", 0.0)),
        "recommendation_confidence": _clamp(quality.get("recommendation_confidence", 0.35) + candidate_adjustments.get("recommendation_confidence", 0.0)),
        "warning_severity": _clamp(_warning_score(bundle.warnings) + candidate_adjustments.get("warning_severity", 0.0)),
        "constraint_pass_rate": _clamp(constraints.get("constraint_pass_rate", 0.35) + candidate_adjustments.get("constraint_pass_rate", 0.0)),
        "mutation_safety": _clamp(mutation_safety_score),
        "identity_preservation": _clamp(identity_preservation_score),
        "modality_agreement_quality": _clamp(modality_agreement_mean + candidate_adjustments.get("modality_agreement_quality", 0.0)),
        "segmentation_confidence": _clamp(transition_confidence_mean - min((false_positive.get("false_positive_boundary_ratio") or 0.0) * 0.24, 0.18) + candidate_adjustments.get("segmentation_confidence", 0.0)),
        "evidence_stability": _clamp((evidence_strength * 0.72) + (consensus_mean * 0.28) + candidate_adjustments.get("evidence_stability", 0.0)),
        "revision_evidence_quality": _clamp((evidence_scores.get("modality_scores", {}).get("revision", {}) or {}).get("score", 0.45) + candidate_adjustments.get("revision_evidence_quality", 0.0)),
        "rhetorical_coherence_score": _clamp(rhetorical_coherence.get("rhetorical_coherence_score", rhetoric.get("rhetorical_balance_score", 0.35))),
        "boundary_diagnostic_quality": _clamp((boundary_diagnostics.get("summary") or {}).get("mean_consensus_support", transition_confidence_mean)),
        "unsupported_shift_penalty": _clamp(1.0 - min(len(topic_continuity.get("unsupported_topic_shifts") or []) * 0.12, 0.6)),
        "unresolved_question_penalty": _clamp(1.0 - min(len(rhetorical_coherence.get("unresolved_questions") or []) * 0.1, 0.5)),
        "claim_without_example_penalty": _clamp(1.0 - min(len(rhetorical_coherence.get("claims_without_examples") or []) * 0.06, 0.42)),
        "discourse_continuity": _clamp((discourse_summary.get("decomposed_scores") or {}).get("discourse_state_continuity", discourse_state.get("discourse_continuity_score", 0.35))),
        "argument_completeness": _clamp(argument_graph.get("argument_completeness_score", 0.35)),
        "callback_resolution_quality": _clamp(callback_resolution.get("payoff_quality_score", 0.35)),
        "narrative_persistence": _clamp(narrative_memory.get("thematic_persistence_score", 0.35)),
        "ambiguity_adjusted_continuity": _clamp(discourse_summary.get("ambiguity_adjusted_continuity", topic_continuity.get("topic_continuity_score", 0.35))),
        "unresolved_discourse_pressure": _clamp(1.0 - discourse_state.get("discourse_pressure_score", 0.0)),
        "contradiction_cluster_pressure": _clamp(1.0 - min(len(argument_graph.get("contradiction_clusters") or []) * 0.12, 0.6)),
        "visual_continuity_quality": _clamp(visual_continuity.get("visual_continuity_score", 0.35) + candidate_adjustments.get("visual_continuity_quality", 0.0)),
        "visual_boundary_alignment_quality": _clamp(visual_structure.get("visual_boundary_alignment_quality", 0.35) + candidate_adjustments.get("visual_boundary_alignment_quality", 0.0)),
        "visual_evidence_completeness": _clamp(visual_structure.get("visual_evidence_completeness", 0.25) + candidate_adjustments.get("visual_evidence_completeness", 0.0)),
        "visual_contradiction_pressure": _clamp(1.0 - (visual_alignment.get("summary") or {}).get("mean_visual_contradiction", 0.35) + candidate_adjustments.get("visual_contradiction_pressure", 0.0)),
        "visual_reset_support": _clamp(visual_structure.get("visual_reset_support", 0.0) + candidate_adjustments.get("visual_reset_support", 0.0)),
        "structural_coherence": _clamp(sequence_summary.get("structural_coherence_score", 0.35)),
        "temporal_rhythm_stability": _clamp(1.0 - _num(sequence_summary.get("mean_intensity_wave_score"), 0.5) * 0.24),
        "editorial_pressure": _clamp(1.0 - _num(sequence_summary.get("peak_cumulative_pressure_score"), 0.5)),
        "recommendation_dependency_pressure": _clamp(1.0 - _num(sequence_summary.get("recommendation_dependency_pressure"), 0.35)),
        "revision_propagation_risk": _clamp(1.0 - _num(sequence_summary.get("mean_propagation_uncertainty"), 0.45)),
        "counterfactual_uncertainty": _clamp(1.0 - _num(sequence_summary.get("mean_counterfactual_uncertainty"), 0.45)),
        "epistemic_stability": _clamp(sequence_summary.get("epistemic_stability_score", 0.35)),
        "creator_stability": _clamp((comparative_outputs.get("creator_evolution") or {}).get("summary", {}).get("creator_stability_score", 0.35)),
        "comparative_volatility": _clamp(1.0 - _num(comparative_summary.get("comparative_volatility"), 0.35)),
        "recurring_structural_debt": _clamp(1.0 - _num((comparative_outputs.get("structural_pattern_mining") or {}).get("summary", {}).get("chronic_pressure_region_count"), 0.0) / 6.0),
    }
    total_weight = sum(weights.values()) or 1.0
    score = _clamp(sum(metrics[key] * weights.get(key, 0.0) for key in metrics) / total_weight)

    blocking = []
    if bundle.transcript.get("transcription_status") != "complete":
        blocking.append("Transcript is not complete; language-derived readiness is limited.")
    for row in constraint_report.get("constraints", []):
        if row.get("status") == "fail" and row.get("constraint_id") in {"no_unlabeled_mutation", "no_render_required_for_minimal_candidate", "no_timing_change_without_explicit_flag"}:
            blocking.append(f"Constraint failed: {row.get('constraint_id')}.")

    weak = sorted(metrics.items(), key=lambda item: (item[1], item[0]))[:3]
    strong = sorted(metrics.items(), key=lambda item: (-item[1], item[0]))[:3]
    non_blocking = [row["constraint_id"] for row in constraint_report.get("constraints", []) if row.get("status") in {"warn", "unavailable"}]
    confidence_changes = [
        {
            "factor": "topic_continuity_score",
            "score": topic_continuity.get("topic_continuity_score", metrics["topic_continuity"]),
            "reason": "Rolling transcript-window continuity now explains unsupported topic shifts.",
        },
        {
            "factor": "rhetorical_coherence_score",
            "score": metrics["rhetorical_coherence_score"],
            "reason": "Question-answer, claim-example, and abstract-concrete gaps now affect readiness.",
        },
        {
            "factor": "boundary_diagnostic_quality",
            "score": metrics["boundary_diagnostic_quality"],
            "reason": "Boundary review evidence now contributes without rewriting segment boundaries.",
        },
        {
            "factor": "modality_agreement_quality",
            "score": metrics["modality_agreement_quality"],
            "reason": "Cross-modal agreement now contributes to release readiness.",
        },
        {
            "factor": "segmentation_confidence",
            "score": metrics["segmentation_confidence"],
            "reason": "Transition confidence is penalized by likely false-positive boundary ratio.",
        },
        {
            "factor": "evidence_stability",
            "score": metrics["evidence_stability"],
            "reason": "Overall evidence strength and consensus score are fused conservatively.",
        },
        {
            "factor": "revision_evidence_quality",
            "score": metrics["revision_evidence_quality"],
            "reason": "Revision artifact completeness and schema validation improve planning confidence.",
        },
        {
            "factor": "ambiguity_adjusted_continuity",
            "score": metrics["ambiguity_adjusted_continuity"],
            "reason": "Low lexical continuity is upgraded only when callback, rhetorical pivot, or illustrative detour evidence supports it.",
        },
        {
            "factor": "unresolved_discourse_pressure",
            "score": metrics["unresolved_discourse_pressure"],
            "reason": "Open questions, deferred claims, pending examples, and unresolved setups reduce readiness until reviewed.",
        },
        {
            "factor": "argument_completeness",
            "score": metrics["argument_completeness"],
            "reason": "Claim/support/takeaway chains now explain why continuity is downgraded or upgraded.",
        },
        {
            "factor": "callback_resolution_quality",
            "score": metrics["callback_resolution_quality"],
            "reason": "Setup/payoff quality now protects intentional callbacks and penalizes unresolved setups.",
        },
        {
            "factor": "visual_boundary_alignment_quality",
            "score": metrics["visual_boundary_alignment_quality"],
            "reason": "Visual boundary evidence now contributes only when it aligns with transcript, discourse, acoustic, or rhetorical evidence.",
        },
        {
            "factor": "visual_contradiction_pressure",
            "score": metrics["visual_contradiction_pressure"],
            "reason": "Visual contradictions reduce readiness because visual resets and discourse boundaries may disagree.",
        },
    ]
    next_action = "Verify transcript and review blocking constraints before planning edits."
    if not blocking:
        next_action = "Inspect the recommended proposal branch and perform human review before any edit application."
    if score >= 0.82 and not blocking:
        next_action = "Prepare a human-reviewed dry run; do not treat heuristic readiness as publication approval."

    return {
        "release_readiness_score": score,
        "release_readiness_class": release_class(score, blocking),
        "score_components": metrics,
        "score_weights": weights,
        "blocking_issues": blocking,
        "non_blocking_warnings": non_blocking,
        "strongest_evidence": [{"metric": key, "score": value} for key, value in strong],
        "weakest_evidence": [{"metric": key, "score": value} for key, value in weak],
        "confidence_change_explanation": confidence_changes,
        "consensus_inputs": {
            "mean_consensus_score": ((consensus.get("summary", {}) or {}).get("consensus_score_distribution", {}) or {}).get("mean"),
            "mean_modality_agreement": (modality_agreement.get("summary", {}) or {}).get("mean_agreement_score"),
            "false_positive_boundary_ratio": false_positive.get("false_positive_boundary_ratio"),
            "transition_confidence_mean": ((transition.get("summary", {}) or {}).get("confidence_distribution", {}) or {}).get("mean"),
            "topic_continuity_score": topic_continuity.get("topic_continuity_score"),
            "rhetorical_coherence_score": rhetorical_coherence.get("rhetorical_coherence_score"),
            "unsupported_shift_count": len(topic_continuity.get("unsupported_topic_shifts") or []),
            "unresolved_question_count": len(rhetorical_coherence.get("unresolved_questions") or []),
            "claim_without_example_count": len(rhetorical_coherence.get("claims_without_examples") or []),
            "discourse_continuity": metrics["discourse_continuity"],
            "argument_completeness": metrics["argument_completeness"],
            "callback_resolution_quality": metrics["callback_resolution_quality"],
            "narrative_persistence": metrics["narrative_persistence"],
            "ambiguity_adjusted_continuity": metrics["ambiguity_adjusted_continuity"],
            "unresolved_discourse_pressure": discourse_state.get("discourse_pressure_score"),
            "contradiction_cluster_count": len(argument_graph.get("contradiction_clusters") or []),
            "visual_continuity_score": visual_continuity.get("visual_continuity_score"),
            "visual_boundary_alignment_quality": visual_structure.get("visual_boundary_alignment_quality"),
            "visual_evidence_completeness": visual_structure.get("visual_evidence_completeness"),
            "visual_contradiction_pressure": (visual_alignment.get("summary") or {}).get("mean_visual_contradiction"),
            "visual_reset_support": visual_structure.get("visual_reset_support"),
        },
        "next_best_action": next_action,
        "limitations": [
            "Release readiness is a conservative heuristic for planning only.",
            "This report does not claim final publication readiness.",
        ],
    }


def summarize_candidate_readiness(candidates: list[dict]) -> dict:
    scores = [row.get("predicted_release_readiness", {}).get("release_readiness_score") for row in candidates]
    scores = [float(value) for value in scores if value is not None]
    return {
        "candidate_count": len(candidates),
        "mean_predicted_score": round(mean(scores), 3) if scores else None,
        "best_score": round(max(scores), 3) if scores else None,
    }
