"""Deterministic mapping from dashboard patterns to video optimization guidance."""

from __future__ import annotations

from intelligence_common import base_artifact
from stability import deterministic_id


GUIDANCE_LIBRARY = {
    "pacing": ("speech_rate_wpm", "Edit pacing", "Slow delivery or add breathing room around dense claims.", "Add natural pauses only where they do not disrupt meaning.", "Re-record compressed phrasing when edits would sound artificial."),
    "speech_delivery": ("speech_rate_wpm", "Clarify argument", "Use shorter clauses and clearer emphasis.", "Trim repetitions only after preserving meaning.", "Re-record unclear sections with stronger phrasing."),
    "pauses": ("silence_ratio", "Add transition", "Place pauses at argument turns.", "Add a pause or title beat where structure changes.", "Re-record only if pauses cannot be edited naturally."),
    "emotional_intensity_arc": ("acoustic_energy_variability", "Accept as intentional style", "Shape intensity so peaks have contrast.", "Smooth harsh peaks or add a visual reset.", "Re-record if intensity is consistently flat or overloaded."),
    "rhetorical_clarity": ("rhetorical_pressure", "Clarify argument", "Separate claims from support.", "Split dense sections or add lower-third labels.", "Re-record with clearer setup/payoff if needed."),
    "argument_structure": ("topic_drift", "Clarify argument", "Add bridge sentences between ideas.", "Reorder or add transitions after review.", "Re-record sections with unresolved argument chains."),
    "examples_concreteness": ("abstract_concrete_balance", "Add example", "Pair abstractions with concrete examples.", "Add visual support or an example card.", "Re-record if the idea needs a simpler concrete explanation."),
    "visual_reset": ("visual_reset_frequency", "Add visual reset", "Plan chaptering or visual support for dense stretches.", "Add B-roll, slide, title card, transition, or camera angle change.", "Re-record only if visual support cannot clarify the section."),
    "shot_structure": ("shot_boundary_density", "Add transition", "Align shot changes with meaning, not arbitrary cadence.", "Adjust cuts or transitions after manual review.", "Re-record only for source-level continuity problems."),
    "topic_continuity": ("topic_drift", "Clarify argument", "Re-enter concepts before moving on.", "Add transition or remove off-path scene after review.", "Re-record confusing bridge material."),
    "boundary_review": ("continuity_score", "Review manually", "Inspect low-confidence boundaries.", "Adjust scene boundaries only after evidence review.", "Re-record is rarely needed unless source structure is unclear."),
    "evidence_confidence": ("evidence_consensus_strength", "Review manually", "Trust high-consensus issues first but inspect evidence.", "Do not edit solely from a weak-consensus signal.", "Re-record only after human confirmation."),
    "governance_readiness": ("readiness_score", "Review manually", "Resolve Tier 1 blockers and threshold gaps.", "No timeline edit is implied by readiness alone.", "Re-record only when a confirmed blocker requires it."),
    "remediation_planning": ("remediation_priority", "Review manually", "Work the highest-priority remediation items first.", "Document accepted risk or false positive decisions locally.", "Re-record only after explicit human decision."),
}


def _status_for(metric_id: str, outputs: dict) -> str:
    summary = outputs.get("corpus_summary") or {}
    intelligence = outputs.get("corpus_intelligence") or {}
    diagnostics = outputs.get("governance_diagnostics") or {}
    if metric_id == "readiness_score":
        score = summary.get("corpus_readiness_score") or 0
        return "concern" if score < 0.68 else "caution" if score < 0.82 else "good"
    if metric_id == "rhetorical_pressure":
        value = (intelligence.get("summary") or {}).get("mean_peak_pressure") or 0
        return "concern" if value >= 0.7 else "caution" if value >= 0.45 else "good"
    if metric_id == "governance_threshold_gap":
        failed = (diagnostics.get("summary") or {}).get("failed_threshold_count") or 0
        return "concern" if failed else "good"
    return "review"


def build_optimization_guidance(outputs: dict | None = None) -> dict:
    outputs = outputs or {}
    rows = []
    for category, (metric, action, production, editing, rerecord) in GUIDANCE_LIBRARY.items():
        status = _status_for(metric, outputs)
        rows.append({
            "guidance_id": deterministic_id("GUIDE", category, metric),
            "category": category,
            "trigger_metric_or_pattern": metric,
            "current_status": status,
            "recommended_action": action,
            "production_action": production,
            "editing_action": editing,
            "re_recording_action": rerecord,
            "preserve_as_intentional_option": "Preserve as-is when the pattern is deliberate, coherent, and supported by human review.",
            "expected_benefit": "Improves reviewer clarity and gives production teams a concrete next action without applying edits automatically.",
            "risk_of_overcorrection": "Overcorrecting can flatten style, reduce energy, or remove intentional rhetorical tension.",
            "human_review_required": True,
            "mutation_required": False,
            "evidence_refs": ["dashboard/graph_interpretation_index.json", "dashboard/expert_metric_ranges.json"],
        })
    output = base_artifact(method="deterministic_optimization_guidance_v1")
    output.update({
        "optimization_guidance_index_id": deterministic_id("OGI", [(row["category"], row["trigger_metric_or_pattern"], row["current_status"]) for row in rows]),
        "guidance_items": rows,
        "summary": {"guidance_item_count": len(rows), "mutation_required": False},
    })
    return output
