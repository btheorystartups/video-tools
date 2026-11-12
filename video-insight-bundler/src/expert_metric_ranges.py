"""Deterministic expert metric guidance ranges for dashboard interpretation."""

from __future__ import annotations

from intelligence_common import base_artifact
from stability import deterministic_id


def _range(metric_id: str, display_name: str, subsystem: str, unit: str, good, caution, concern, direction: str, notes: list[str], guidance: list[str], limitations: list[str]) -> dict:
    return {
        "metric_id": metric_id,
        "display_name": display_name,
        "subsystem": subsystem,
        "unit": unit,
        "good_range": good,
        "caution_range": caution,
        "concern_range": concern,
        "lower_is_better": direction == "lower_is_better",
        "higher_is_better": direction == "higher_is_better",
        "balanced_is_better": direction == "balanced_is_better",
        "interpretation_notes": notes,
        "optimization_guidance": guidance,
        "limitations": limitations,
    }


def build_expert_metric_ranges() -> dict:
    """Return conservative editorial heuristics used by Phase 31 dashboards."""
    rows = [
        _range("speech_rate_wpm", "Speech rate", "speech_pacing", "words_per_minute", {"min": 115, "max": 165}, {"low": "<115", "high": "166-190"}, {"high": ">190"}, "balanced_is_better", ["Treat as delivery pacing, not comprehension proof."], ["Preserve if clear and energetic; slow delivery or add natural breathing room when compressed."], ["Different genres, speakers, and audiences tolerate different rates."]),
        _range("pause_density", "Pause density", "speech_pacing", "pauses_per_minute", {"qualitative": "balanced"}, {"qualitative": "low or elevated"}, {"qualitative": "extreme"}, "balanced_is_better", ["Pauses help segmentation and emphasis when they align with meaning."], ["Add visual or verbal breaks around dense claims."], ["Low pause density does not prove poor quality."]),
        _range("silence_ratio", "Silence ratio", "speech_pacing", "ratio", {"min": 0.08, "max": 0.28}, {"low": "0.03-0.079", "high": "0.281-0.38"}, {"low": "<0.03", "high": ">0.38"}, "balanced_is_better", ["Very low silence can indicate compressed pacing; very high silence can indicate drag."], ["Edit pacing, add transitions, or preserve quiet style if intentional."], ["Silence can be stylistic, technical, or contextual."]),
        _range("acoustic_energy_variability", "Acoustic energy variability", "acoustic", "normalized", {"qualitative": "balanced"}, {"qualitative": "low or elevated"}, {"qualitative": "flat or extreme"}, "balanced_is_better", ["Variation can support emphasis and attention."], ["Re-record flat sections or smooth harsh peaks."], ["Energy proxies do not identify emotional state."]),
        _range("segment_duration", "Segment duration", "segment_timeline", "seconds", {"qualitative": "varied with clear boundaries"}, {"qualitative": "long runs or over-fragmented"}, {"qualitative": "unbroken dense sections"}, "balanced_is_better", ["Segment lengths should follow argument structure."], ["Split dense sections, add transitions, or preserve if intentionally long-form."], ["No universal ideal segment length exists."]),
        _range("topic_drift", "Topic drift", "discourse", "normalized", {"max": 0.35}, {"min": 0.351, "max": 0.6}, {"min": 0.601}, "lower_is_better", ["High drift suggests transitions may need review."], ["Clarify bridge language or reorder supporting examples."], ["Topic proxies do not prove contradiction or truth."]),
        _range("rhetorical_pressure", "Rhetorical pressure", "rhetorical", "normalized", {"max": 0.45}, {"min": 0.451, "max": 0.7}, {"min": 0.701}, "lower_is_better", ["Pressure rises when claims, unresolved chains, or density cluster."], ["Clarify argument, add examples, or add a reset."], ["High pressure can be intentional intensity."]),
        _range("claim_density", "Claim density", "rhetorical", "qualitative", {"qualitative": "balanced"}, {"qualitative": "elevated"}, {"qualitative": "high"}, "balanced_is_better", ["Claims need enough support and pacing."], ["Add examples, evidence, or clearer setup/payoff."], ["Claim density does not evaluate truth."]),
        _range("question_density", "Question density", "rhetorical", "qualitative", {"qualitative": "purposeful"}, {"qualitative": "elevated"}, {"qualitative": "high without payoff"}, "balanced_is_better", ["Questions can frame attention but need resolution."], ["Resolve rhetorical questions or reduce repetition."], ["Questions are stylistic, not quality failures by themselves."]),
        _range("example_density", "Example density", "rhetorical", "qualitative", {"qualitative": "sufficient examples near abstract claims"}, {"qualitative": "thin"}, {"qualitative": "very low"}, "higher_is_better", ["Examples can make abstract ideas inspectable."], ["Add concrete examples or visual support."], ["Abstract style can be intentional."]),
        _range("abstract_concrete_balance", "Abstract/concrete balance", "rhetorical", "qualitative", {"qualitative": "balanced"}, {"qualitative": "abstract-leaning or example-heavy"}, {"qualitative": "highly abstract with low examples"}, "balanced_is_better", ["Balance helps audiences track concepts."], ["Add concrete example, visual support, or clarify claim."], ["Do not remove abstraction when it is the intended style."]),
        _range("visual_reset_frequency", "Visual reset frequency", "visual", "qualitative", {"qualitative": "regular resets at topic or intensity changes"}, {"qualitative": "sparse"}, {"qualitative": "very low through dense sections"}, "balanced_is_better", ["Visual resets can mark chapters and reduce monotony."], ["Add B-roll, title card, slide, angle change, or transition."], ["Minimalist monologue can be intentional."]),
        _range("shot_boundary_density", "Shot boundary density", "visual", "qualitative", {"qualitative": "matches pacing"}, {"qualitative": "low or high"}, {"qualitative": "mismatched with content density"}, "balanced_is_better", ["Shot changes should support structure."], ["Add or remove transitions after manual review."], ["Shot proxies do not analyze faces, identity, or intent."]),
        _range("continuity_score", "Continuity score", "visual", "normalized", {"min": 0.7}, {"min": 0.5, "max": 0.699}, {"max": 0.499}, "higher_is_better", ["Low continuity can point to abrupt or unsupported shifts."], ["Review boundaries and add transitional context."], ["Continuity is a proxy, not a semantic truth claim."]),
        _range("evidence_consensus_strength", "Evidence consensus strength", "evidence", "normalized", {"min": 0.75}, {"min": 0.5, "max": 0.749}, {"max": 0.499}, "higher_is_better", ["Consensus is stronger when independent local artifacts agree."], ["Prioritize high-consensus items for review."], ["Consensus does not prove correctness."]),
        _range("blocker_severity", "Blocker severity", "governance", "tier", {"qualitative": "no Tier 1 blockers"}, {"qualitative": "Tier 2 review items"}, {"qualitative": "unresolved Tier 1 blockers"}, "lower_is_better", ["Tier 1 items block promotion until human disposition."], ["Review evidence and record valid decisions."], ["The system does not clear blockers automatically."]),
        _range("review_queue_tier", "Review queue tier", "editorial", "tier", {"qualitative": "Tier 3 or empty"}, {"qualitative": "Tier 2"}, {"qualitative": "Tier 1"}, "lower_is_better", ["Higher tiers deserve earlier human attention."], ["Work Tier 1 evidence first."], ["Tiers prioritize review, not edits."]),
        _range("readiness_score", "Readiness score", "governance", "normalized", {"min": 0.82}, {"min": 0.68, "max": 0.819}, {"max": 0.679}, "higher_is_better", ["Readiness aggregates local evidence conservatively."], ["Resolve threshold gaps and reassess."], ["Readiness does not predict viewer behavior."]),
        _range("governance_threshold_gap", "Governance threshold gap", "governance", "normalized", {"max": 0.0}, {"min": 0.001, "max": 0.2}, {"min": 0.201}, "lower_is_better", ["Gaps show what prevents promotion."], ["Address largest blocking gap first."], ["Some gaps require human review rather than edits."]),
        _range("remediation_priority", "Remediation priority", "remediation", "score", {"qualitative": "low"}, {"qualitative": "medium"}, {"qualitative": "high"}, "lower_is_better", ["Priority orders review effort."], ["Plan remediation before production changes."], ["Remediation items do not mutate media."]),
    ]
    output = base_artifact(method="deterministic_expert_metric_ranges_v1")
    output.update({
        "expert_metric_ranges_id": deterministic_id("EMR", [(row["metric_id"], row["good_range"], row["concern_range"]) for row in rows]),
        "metric_ranges": rows,
        "summary": {"metric_range_count": len(rows)},
    })
    return output
