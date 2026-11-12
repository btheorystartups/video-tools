"""Deterministic editorial constraint evaluation for revision planning."""

from __future__ import annotations

from typing import Any


DEFAULT_THRESHOLDS = {
    "max_questionable_boundary_ratio": 0.25,
    "min_transcript_quality": 0.65,
    "min_recommendation_confidence": 0.58,
    "max_topic_drift_score": 0.7,
    "min_rhetorical_balance_score": 0.35,
    "max_silence_ratio": 0.42,
    "max_pacing_variability": 85.0,
    "min_emotional_continuity": 0.55,
    "min_segmentation_smoothness": 0.55,
    "max_identity_change_risk": 0.25,
    "minimum_consensus_score": 0.48,
    "max_false_positive_boundary_ratio": 0.28,
    "min_modality_agreement": 0.55,
    "min_transition_confidence": 0.45,
    "max_evidence_instability": 0.52,
}


def _thresholds(profile: dict | None) -> dict:
    merged = dict(DEFAULT_THRESHOLDS)
    merged.update((profile or {}).get("constraint_thresholds") or {})
    return merged


def _num(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _pressure(value: float | None, threshold: float, direction: str) -> float:
    if value is None:
        return 0.55
    if direction == "min":
        if value >= threshold:
            return round(max(0.0, (threshold - value) / max(threshold, 1e-9)), 3)
        return round(min(1.0, (threshold - value) / max(threshold, 1e-9)), 3)
    if value <= threshold:
        return round(max(0.0, value / max(threshold, 1e-9) - 0.75), 3)
    return round(min(1.0, (value - threshold) / max(threshold, 1e-9)), 3)


def _status(value: float | None, threshold: float, direction: str) -> str:
    if value is None:
        return "unavailable"
    if direction == "min":
        if value >= threshold:
            return "pass"
        return "warn" if value >= threshold * 0.82 else "fail"
    if value <= threshold:
        return "pass"
    return "warn" if value <= threshold * 1.2 else "fail"


def _constraint(
    constraint_id: str,
    label: str,
    value: float | None,
    threshold: float,
    direction: str,
    affected_artifacts: list[str],
    evidence: list[str],
) -> dict:
    return {
        "constraint_id": constraint_id,
        "label": label,
        "current_value": None if value is None else round(value, 3),
        "threshold": threshold,
        "direction": "<=" if direction == "max" else ">=",
        "status": _status(value, threshold, direction),
        "pressure_score": _pressure(value, threshold, direction),
        "affected_artifacts": affected_artifacts,
        "evidence": evidence,
    }


def evaluate_editorial_constraints(bundle, report_data: dict, revision_profile: dict | None = None, candidate: dict | None = None) -> dict:
    """Return deterministic constraint records for the observed or simulated state."""

    thresholds = _thresholds(revision_profile)
    segments = bundle.scene_segments.get("segments") or []
    questionable = [row for row in segments if (row.get("boundary") or {}).get("questionable")]
    quality = report_data.get("quality_scores", {})
    topic = getattr(bundle, "topic_analysis", None) or {}
    rhetoric = getattr(bundle, "rhetorical_analysis", None) or {}
    acoustic = getattr(bundle, "acoustic_features", None) or {}
    pacing = report_data.get("pacing_statistics", {})
    consensus_outputs = getattr(bundle, "consensus_outputs", None) or {}
    consensus = consensus_outputs.get("evidence_consensus") or {}
    transition = consensus_outputs.get("transition_confidence") or {}
    modality_agreement = consensus_outputs.get("modality_agreement") or {}
    false_positive = consensus_outputs.get("false_positive_boundaries") or {}
    evidence_scores = consensus_outputs.get("evidence_score_summary") or {}
    candidate = candidate or {}

    render_required = bool(candidate.get("render_required", False))
    timing_change = any(change.get("change_type") == "timing" for change in candidate.get("proposed_changes") or [])
    explicit_timing_flag = any(change.get("explicit_timing_change") for change in candidate.get("proposed_changes") or [])
    mutation_labelled = bool(candidate.get("mutation_safety_class") or not candidate)
    identity_risk = _num(candidate.get("identity_change_risk"))
    if identity_risk is None:
        identity_score = _num(candidate.get("identity_preservation_score"))
        identity_risk = None if identity_score is None else max(0.0, 1.0 - identity_score)
    if identity_risk is None:
        identity_risk = 0.0

    boundary_ratio = len(questionable) / max(len(segments), 1) if segments else None
    constraints = [
        _constraint(
            "max_questionable_boundary_ratio",
            "Questionable boundary ratio",
            boundary_ratio,
            thresholds["max_questionable_boundary_ratio"],
            "max",
            ["scene_segments.json", "reports/segment_boundary_report.json"],
            [f"{len(questionable)} questionable boundaries across {len(segments)} segments."],
        ),
        _constraint("min_transcript_quality", "Transcript quality", _num(quality.get("transcript_quality")), thresholds["min_transcript_quality"], "min", ["transcript.json", "reports/quality_report.json"], [f"Transcript status is {bundle.transcript.get('transcription_status')}."]),
        _constraint("min_recommendation_confidence", "Recommendation confidence", _num(quality.get("recommendation_confidence")), thresholds["min_recommendation_confidence"], "min", ["recommendations.json", "reports/quality_report.json"], ["Evidence-ranked recommendations are heuristic."]),
        _constraint("max_topic_drift_score", "Topic drift", _num(topic.get("topic_drift_score")), thresholds["max_topic_drift_score"], "max", ["topic_analysis.json"], ["Lower drift suggests stronger continuity."]),
        _constraint("min_rhetorical_balance_score", "Rhetorical balance", _num(rhetoric.get("rhetorical_balance_score")), thresholds["min_rhetorical_balance_score"], "min", ["rhetorical_analysis.json"], ["Claim/example and abstract/concrete balance are marker-based."]),
        _constraint("max_silence_ratio", "Silence ratio", _num(acoustic.get("silence_ratio")), thresholds["max_silence_ratio"], "max", ["acoustic_features.json"], ["Silence ratio is unavailable when acoustic analysis is unavailable."]),
        _constraint("max_pacing_variability", "Pacing variability", _num(pacing.get("pacing_volatility")), thresholds["max_pacing_variability"], "max", ["audio_features.json", "reports/pacing_statistics.json"], ["Pacing volatility is transcript-timing derived."]),
        _constraint("min_emotional_continuity", "Emotional continuity", _num(quality.get("emotional_continuity")), thresholds["min_emotional_continuity"], "min", ["emotional_arc.json"], ["Continuity is derived from deterministic emotional arc heuristics."]),
        _constraint("min_segmentation_smoothness", "Segmentation smoothness", _num(quality.get("segmentation_smoothness")), thresholds["min_segmentation_smoothness"], "min", ["scene_segments.json"], ["Smoothness is derived from segment duration consistency."]),
        _constraint("max_identity_change_risk", "Identity change risk", identity_risk, thresholds["max_identity_change_risk"], "max", ["revision_graph/revision_candidates.json"], ["Proposal-only branches must preserve editorial identity unless explicitly reviewed."]),
        _constraint("minimum_consensus_score", "Minimum consensus score", _num(((consensus.get("summary", {}) or {}).get("consensus_score_distribution", {}) or {}).get("mean")), thresholds["minimum_consensus_score"], "min", ["consensus/evidence_consensus.json"], ["Consensus score fuses visible local modalities for review."]),
        _constraint("max_false_positive_boundary_ratio", "False-positive boundary ratio", _num(false_positive.get("false_positive_boundary_ratio")), thresholds["max_false_positive_boundary_ratio"], "max", ["consensus/false_positive_boundaries.json"], ["False-positive boundaries are flagged, not removed."]),
        _constraint("min_modality_agreement", "Modality agreement", _num((modality_agreement.get("summary", {}) or {}).get("mean_agreement_score")), thresholds["min_modality_agreement"], "min", ["consensus/modality_agreement.json"], ["Pairwise modality agreement supports release-readiness explainability."]),
        _constraint("min_transition_confidence", "Transition confidence", _num(((transition.get("summary", {}) or {}).get("confidence_distribution", {}) or {}).get("mean")), thresholds["min_transition_confidence"], "min", ["consensus/transition_confidence.json"], ["Transition confidence fuses pauses, topic, rhetoric, acoustic, pacing, and emotional shifts."]),
        _constraint("max_evidence_instability", "Evidence instability", None if evidence_scores.get("overall_evidence_strength") is None else 1.0 - _num(evidence_scores.get("overall_evidence_strength")), thresholds["max_evidence_instability"], "max", ["consensus/evidence_score_summary.json"], ["Evidence instability is the inverse of deterministic evidence strength."]),
    ]

    boolean_constraints = [
        ("no_unlabeled_mutation", mutation_labelled, "All proposed changes have mutation safety labels."),
        ("no_render_required_for_minimal_candidate", not (candidate.get("candidate_label") == "Candidate_A_Minimal" and render_required), "Minimal candidate must not require rendering."),
        ("no_timing_change_without_explicit_flag", not timing_change or explicit_timing_flag, "Timing changes require an explicit flag."),
    ]
    for constraint_id, passed, evidence in boolean_constraints:
        constraints.append(
            {
                "constraint_id": constraint_id,
                "label": constraint_id.replace("_", " ").title(),
                "current_value": bool(passed),
                "threshold": True,
                "direction": "==",
                "status": "pass" if passed else "fail",
                "pressure_score": 0.0 if passed else 1.0,
                "affected_artifacts": ["revision_graph/mutation_safety_contract.json"],
                "evidence": [evidence],
            }
        )

    counts = {status: sum(1 for row in constraints if row["status"] == status) for status in ["pass", "warn", "fail", "unavailable"]}
    pass_rate = round((counts["pass"] + counts["warn"] * 0.6 + counts["unavailable"] * 0.35) / max(len(constraints), 1), 3)
    return {
        "constraint_profile": (revision_profile or {}).get("profile_name", "default_conservative_revision_profile"),
        "constraints": constraints,
        "summary": {
            "constraint_count": len(constraints),
            "status_counts": counts,
            "constraint_pass_rate": pass_rate,
            "highest_pressure_constraints": sorted(
                [{"constraint_id": row["constraint_id"], "pressure_score": row["pressure_score"], "status": row["status"]} for row in constraints],
                key=lambda row: (-row["pressure_score"], row["constraint_id"]),
            )[:5],
        },
    }
