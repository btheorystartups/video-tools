"""Multimodal evidence consensus generation for local analysis artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

from evidence_scoring import build_evidence_score_summary
from stability import write_json
from transition_confidence import build_transition_confidence


MODALITY_PAIRS = [
    ("topic", "rhetorical"),
    ("rhetorical", "acoustic"),
    ("acoustic", "pacing"),
    ("visual", "transcript"),
    ("visual", "rhetorical"),
    ("visual", "discourse"),
    ("emotional", "rhetorical"),
    ("topic", "emotional"),
    ("pacing", "segmentation"),
]


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _avg(values: list[float]) -> float:
    clean = [float(value) for value in values if value is not None]
    return round(mean(clean), 3) if clean else 0.0


def _consensus_class(score: float, conflict_count: int, modality_count: int) -> str:
    if modality_count < 2:
        return "insufficient_evidence"
    if conflict_count >= 3:
        return "disagreement"
    if score >= 0.76:
        return "strong_agreement"
    if score >= 0.58:
        return "moderate_agreement"
    if score >= 0.4:
        return "weak_agreement"
    return "insufficient_evidence"


def _distribution(values: list[float]) -> dict:
    clean = [float(value) for value in values if value is not None]
    if not clean:
        return {"count": 0, "min": None, "max": None, "mean": None}
    return {"count": len(clean), "min": round(min(clean), 3), "max": round(max(clean), 3), "mean": round(mean(clean), 3)}


def _signal_map(transition: dict) -> dict[str, float]:
    scores = transition.get("evidence_scores") or {}
    return {
        "transcript": _num(scores.get("transcript_pause"), 0.35),
        "segmentation": _num(transition.get("confidence_score"), 0.35),
        "acoustic": _num(scores.get("acoustic_energy_change"), 0.35),
        "rhetorical": _num(scores.get("rhetorical_shift"), 0.35),
        "topic": _num(scores.get("topic_shift"), 0.35),
        "pacing": _num(scores.get("pacing_shift"), 0.35),
        "emotional": _num(scores.get("emotional_transition"), 0.35),
        "visual": _num(scores.get("visual_boundary_support"), 0.35),
        "discourse": _num(scores.get("discourse_boundary_support"), 0.35),
    }


def _inject_visual_scores(transition_report: dict, bundle) -> dict:
    visual_alignment = getattr(bundle, "visual_boundary_alignment", None) or {}
    by_pair = {
        (row.get("from_segment_id"), row.get("to_segment_id")): row
        for row in visual_alignment.get("boundaries", [])
    }
    if not by_pair:
        return transition_report
    copied = dict(transition_report)
    transitions = []
    for row in transition_report.get("transitions", []):
        updated = dict(row)
        alignment = by_pair.get((row.get("from_segment_id"), row.get("to_segment_id")), {})
        if alignment:
            scores = dict(updated.get("evidence_scores") or {})
            scores["visual_boundary_support"] = alignment.get("visual_support")
            scores["visual_contradiction"] = alignment.get("visual_contradiction")
            scores["discourse_boundary_support"] = alignment.get("discourse_support")
            updated["evidence_scores"] = scores
            if alignment.get("visual_support", 0) >= 0.55:
                updated.setdefault("supporting_evidence", []).append({"modality": "visual_boundary_support", "score": alignment.get("visual_support")})
            if alignment.get("visual_contradiction", 0) >= 0.45:
                updated.setdefault("conflicting_evidence", []).append({"modality": "visual_contradiction", "score": alignment.get("visual_contradiction")})
            updated["visual_boundary_alignment"] = {
                "alignment_id": alignment.get("alignment_id"),
                "visual_support": alignment.get("visual_support"),
                "visual_contradiction": alignment.get("visual_contradiction"),
                "boundary_evidence_type": alignment.get("boundary_evidence_type"),
                "suggested_review_action": alignment.get("suggested_review_action"),
            }
        transitions.append(updated)
    copied["transitions"] = transitions
    copied.setdefault("summary", {})["visual_evidence_integrated"] = True
    return copied


def build_evidence_consensus(bundle) -> dict:
    """Build deterministic consensus artifacts and summaries from existing local evidence."""

    transition_report = build_transition_confidence(
        bundle.scene_segments,
        bundle.audio_features,
        getattr(bundle, "acoustic_features", None) or {},
        getattr(bundle, "topic_analysis", None) or {},
        getattr(bundle, "rhetorical_analysis", None) or {},
        bundle.emotional_arc,
    )
    transition_report = _inject_visual_scores(transition_report, bundle)
    evidence_score_summary = build_evidence_score_summary(bundle, transition_report)
    continuity_analysis = transition_report["continuity_analysis"]
    false_positive_boundaries = transition_report["false_positive_boundaries"]
    modality_agreement = build_modality_agreement(transition_report)
    modality_disagreement = build_modality_disagreement(modality_agreement)
    evidence_consensus = _build_consensus_rows(transition_report, continuity_analysis, evidence_score_summary, bundle)

    return {
        "evidence_consensus": evidence_consensus,
        "transition_confidence": {k: v for k, v in transition_report.items() if k not in {"false_positive_boundaries", "continuity_analysis"}},
        "false_positive_boundaries": false_positive_boundaries,
        "continuity_analysis": continuity_analysis,
        "modality_agreement": modality_agreement,
        "modality_disagreement": modality_disagreement,
        "evidence_score_summary": evidence_score_summary,
    }


def _build_consensus_rows(transition_report: dict, continuity_analysis: dict, evidence_score_summary: dict, bundle=None) -> dict:
    continuity_by_id = {row.get("transition_id"): row for row in continuity_analysis.get("continuity_rows", [])}
    modality_strength = {
        key: _num(value.get("score"), 0.35)
        for key, value in (evidence_score_summary.get("modality_scores") or {}).items()
    }
    rows = []
    discourse_summary = getattr(bundle, "discourse_summary", None) or {}
    argument_graph = getattr(bundle, "argument_graph", None) or {}
    callback_resolution = getattr(bundle, "callback_resolution", None) or {}
    narrative_memory = getattr(bundle, "narrative_memory", None) or {}
    editorial_ambiguity = getattr(bundle, "editorial_ambiguity", None) or {}
    sequence_outputs = getattr(bundle, "sequence_outputs", None) or {}
    comparative_outputs = getattr(bundle, "comparative_outputs", None) or {}
    sequence_summary = sequence_outputs.get("sequence_summary") or {}
    comparative_summary = comparative_outputs.get("comparative_summary") or {}
    ambiguity_by_pair = {
        (row.get("from_segment_id"), row.get("to_segment_id")): row
        for row in editorial_ambiguity.get("ambiguity_regions", [])
    }
    unresolved_segments = {
        segment_id
        for chain in argument_graph.get("unresolved_chains", [])
        for segment_id in chain.get("segment_ids", [])
    }
    callback_to = {}
    for row in callback_resolution.get("callback_pairs", []):
        callback_to.setdefault(row.get("payoff_segment_id"), []).append(row)
    memory_to = {}
    for row in narrative_memory.get("callback_references", []):
        memory_to.setdefault(row.get("to_segment_id"), []).append(row)
    for transition in transition_report.get("transitions", []):
        signals = _signal_map(transition)
        supporting = [key for key, value in signals.items() if value >= 0.55 and modality_strength.get(key, 0.35) >= 0.38]
        conflicting = [key for key, value in signals.items() if value <= 0.28]
        weak = [key for key, value in modality_strength.items() if value < 0.42 and key in {"transcript", "segmentation", "acoustic", "rhetorical", "topic", "emotional"}]
        support_score = _avg([signals[key] * modality_strength.get(key, 0.35) for key in supporting]) if supporting else 0.25
        conflict_penalty = min(len(conflicting) * 0.08, 0.28)
        continuity = continuity_by_id.get(transition.get("transition_id"), {})
        topic_cont = _num(continuity.get("topic_continuity"), 1.0 - signals.get("topic", 0.35))
        rhet_cont = _num(continuity.get("rhetorical_continuity"), 1.0 - signals.get("rhetorical", 0.35))
        continuity_confidence = _num(continuity.get("continuity_confidence"), 0.45)
        pair = (transition.get("from_segment_id"), transition.get("to_segment_id"))
        ambiguity_row = ambiguity_by_pair.get(pair, {})
        callback_count = len(callback_to.get(transition.get("to_segment_id"), []))
        narrative_return_count = len(memory_to.get(transition.get("to_segment_id"), []))
        discourse_bonus = 0.0
        if ambiguity_row.get("ambiguity_class") in {"callback_supported_drift", "rhetorical_pivot", "illustrative_detour", "likely_intentional_tangent"}:
            discourse_bonus += 0.08
        if callback_count:
            discourse_bonus += min(callback_count * 0.035, 0.08)
        if narrative_return_count:
            discourse_bonus += min(narrative_return_count * 0.025, 0.06)
        if transition.get("to_segment_id") in unresolved_segments or transition.get("from_segment_id") in unresolved_segments:
            discourse_bonus -= 0.08
        false_positive = _num(transition.get("confidence_score"), 0.0)
        false_positive_probability = _clamp(0.62 - (false_positive * 0.42) + (0.16 if transition.get("likely_false_positive") else 0.0) + (0.1 if transition.get("continuity_override") else 0.0))
        consensus_score = _clamp(support_score * 0.5 + _num(transition.get("confidence_score"), 0.35) * 0.32 + (1.0 - false_positive_probability) * 0.18 - conflict_penalty + discourse_bonus)
        dominant = sorted(supporting, key=lambda key: (-signals[key], key))[:3]
        rows.append(
            {
                "segment_id": transition.get("to_segment_id"),
                "transition_id": transition.get("transition_id"),
                "from_segment_id": transition.get("from_segment_id"),
                "to_segment_id": transition.get("to_segment_id"),
                "consensus_score": consensus_score,
                "consensus_class": _consensus_class(consensus_score, len(conflicting), len(supporting) + len(conflicting)),
                "transition_interpretation": _transition_interpretation(transition, topic_cont, rhet_cont, len(conflicting), ambiguity_row, callback_count, narrative_return_count, unresolved_segments),
                "supporting_modalities": supporting,
                "conflicting_modalities": conflicting,
                "dominant_evidence": dominant,
                "weak_evidence": weak,
                "evidence_strength": _avg([modality_strength.get(key, 0.35) for key in supporting]) if supporting else 0.25,
                "continuity_confidence": continuity_confidence,
                "false_positive_probability": false_positive_probability,
                "evidence_notes": _evidence_notes(transition, supporting, conflicting, continuity),
                "discourse_consensus_inputs": {
                    "discourse_continuity": (discourse_summary.get("decomposed_scores") or {}).get("discourse_state_continuity"),
                    "argument_completeness": argument_graph.get("argument_completeness_score"),
                    "callback_strength": callback_resolution.get("callback_strength_score"),
                    "narrative_persistence": narrative_memory.get("thematic_persistence_score"),
                    "ambiguity_class": ambiguity_row.get("ambiguity_class"),
                    "callback_count": callback_count,
                    "narrative_return_count": narrative_return_count,
                    "discourse_adjustment": round(discourse_bonus, 3),
                },
                "sequence_consensus_inputs": {
                    "structural_sequence_support": sequence_summary.get("structural_coherence_score"),
                    "temporal_rhythm_alignment": sequence_summary.get("mean_intensity_wave_score"),
                    "narrative_phase_alignment": (sequence_outputs.get("narrative_phase_model") or {}).get("summary", {}).get("phase_coverage_score"),
                    "editorial_pressure": sequence_summary.get("peak_cumulative_pressure_score"),
                    "recommendation_interaction_pressure": sequence_summary.get("recommendation_dependency_pressure"),
                    "propagation_uncertainty": sequence_summary.get("mean_propagation_uncertainty"),
                    "creator_level_stability": (comparative_outputs.get("creator_evolution") or {}).get("summary", {}).get("creator_stability_score"),
                    "comparative_continuity_stability": (comparative_outputs.get("multi_video_analysis") or {}).get("summary", {}).get("mean_structural_coherence"),
                    "recurring_discourse_pressure": (comparative_outputs.get("discourse_fingerprint") or {}).get("summary", {}).get("mean_discourse_pressure"),
                },
                "limitations": [
                    "Consensus is evidence fusion for review, not a semantic truth guarantee.",
                    "No boundary or media artifact is changed by this report.",
                ],
            }
        )
    class_counts: dict[str, int] = {}
    for row in rows:
        class_counts[row["consensus_class"]] = class_counts.get(row["consensus_class"], 0) + 1
    return {
        "analysis_status": "complete" if rows else "limited",
        "method": "deterministic_multimodal_evidence_consensus_v1",
        "consensus_items": rows,
        "summary": {
            "consensus_item_count": len(rows),
            "consensus_score_distribution": _distribution([row["consensus_score"] for row in rows]),
            "consensus_class_counts": dict(sorted(class_counts.items())),
            "mean_false_positive_probability": _distribution([row["false_positive_probability"] for row in rows]).get("mean"),
            "weakest_items": sorted(
                [{"transition_id": row["transition_id"], "score": row["consensus_score"], "class": row["consensus_class"]} for row in rows],
                key=lambda row: (row["score"], row["transition_id"] or ""),
            )[:5],
            "strongest_items": sorted(
                [{"transition_id": row["transition_id"], "score": row["consensus_score"], "class": row["consensus_class"]} for row in rows],
                key=lambda row: (-row["score"], row["transition_id"] or ""),
            )[:5],
            "sequence_consensus_inputs": {
                "structural_sequence_support": sequence_summary.get("structural_coherence_score"),
                "temporal_rhythm_alignment": sequence_summary.get("mean_intensity_wave_score"),
                "narrative_phase_alignment": (sequence_outputs.get("narrative_phase_model") or {}).get("summary", {}).get("phase_coverage_score"),
                "editorial_pressure": sequence_summary.get("peak_cumulative_pressure_score"),
                "recommendation_interaction_pressure": sequence_summary.get("recommendation_dependency_pressure"),
                "propagation_uncertainty": sequence_summary.get("mean_propagation_uncertainty"),
                "creator_level_stability": (comparative_outputs.get("creator_evolution") or {}).get("summary", {}).get("creator_stability_score"),
                "comparative_continuity_stability": (comparative_outputs.get("multi_video_analysis") or {}).get("summary", {}).get("mean_structural_coherence"),
                "recurring_contradiction_regions": (comparative_outputs.get("structural_pattern_mining") or {}).get("recurring_contradiction_regions", []),
                "recurring_discourse_pressure": (comparative_outputs.get("discourse_fingerprint") or {}).get("summary", {}).get("mean_discourse_pressure"),
            },
        },
        "limitations": [
            "Consensus outputs are deterministic evidence-fusion heuristics intended to improve explainability and editorial review.",
            "They are not semantic truth guarantees or autonomous editorial decisions.",
        ],
    }


def _transition_interpretation(
    transition: dict,
    topic_continuity: float,
    rhetorical_continuity: float,
    conflict_count: int,
    ambiguity_row: dict | None = None,
    callback_count: int = 0,
    narrative_return_count: int = 0,
    unresolved_segments: set[str] | None = None,
) -> str:
    ambiguity_row = ambiguity_row or {}
    unresolved_segments = unresolved_segments or set()
    klass = ambiguity_row.get("ambiguity_class")
    if klass in {"callback_supported_drift", "rhetorical_pivot", "illustrative_detour", "likely_intentional_tangent"}:
        return {
            "callback_supported_drift": "delayed_rhetorical_payoff",
            "rhetorical_pivot": "intentional_rhetorical_drift",
            "illustrative_detour": "exploratory_tangent",
            "likely_intentional_tangent": "intentional_rhetorical_drift",
        }.get(klass, "intentional_rhetorical_drift")
    if transition.get("from_segment_id") in unresolved_segments or transition.get("to_segment_id") in unresolved_segments:
        return "unresolved_argument_chain"
    if callback_count or narrative_return_count:
        return "recovered_continuity"
    if topic_continuity < 0.38 and rhetorical_continuity < 0.45 and transition.get("confidence_score", 0) >= 0.5:
        return "true_transition"
    if topic_continuity < 0.38 and rhetorical_continuity >= 0.62:
        return "rhetorical_continuation_despite_topic_shift"
    if topic_continuity >= 0.62 and transition.get("evidence_scores", {}).get("acoustic_energy_change", 0) >= 0.55:
        return "topic_continuation_despite_acoustic_shift"
    if topic_continuity < 0.34 and transition.get("confidence_score", 0) < 0.48:
        return "incoherent_drift"
    if conflict_count >= 3 or transition.get("likely_false_positive"):
        return "boundary_needing_human_review"
    return "weak_transition"


def _evidence_notes(transition: dict, supporting: list[str], conflicting: list[str], continuity: dict) -> list[str]:
    notes = []
    if supporting:
        notes.append("Supporting modalities: " + ", ".join(supporting) + ".")
    if conflicting:
        notes.append("Conflicting or continuity-preserving modalities: " + ", ".join(conflicting) + ".")
    if transition.get("continuity_override"):
        notes.append("Continuity override is active; review this boundary before treating it as a true transition.")
    if transition.get("likely_false_positive"):
        notes.append("Transition has false-positive risk based on isolated or weak evidence.")
    if continuity.get("notes"):
        notes.extend(continuity.get("notes")[:2])
    return notes or ["No strong cross-modal agreement; review context manually."]


def build_modality_agreement(transition_report: dict) -> dict:
    rows = transition_report.get("transitions") or []
    pair_rows = []
    for left, right in MODALITY_PAIRS:
        scored = []
        for row in rows:
            signals = _signal_map(row)
            left_score = signals.get(left, signals.get("segmentation", 0.35))
            right_score = signals.get(right, signals.get("segmentation", 0.35))
            agreement = _clamp(1.0 - abs(left_score - right_score))
            scored.append(
                {
                    "transition_id": row.get("transition_id"),
                    "from_segment_id": row.get("from_segment_id"),
                    "to_segment_id": row.get("to_segment_id"),
                    "agreement": agreement,
                    "disagreement": _clamp(1.0 - agreement),
                }
            )
        pair_rows.append(
            {
                "modality_pair": f"{left}_vs_{right}",
                "left_modality": left,
                "right_modality": right,
                "agreement_score": _avg([item["agreement"] for item in scored]),
                "disagreement_score": _avg([item["disagreement"] for item in scored]),
                "strongest_supporting_segments": sorted(scored, key=lambda item: (-item["agreement"], item["transition_id"] or ""))[:5],
                "weakest_segments": sorted(scored, key=lambda item: (item["agreement"], item["transition_id"] or ""))[:5],
                "confidence": _clamp(_avg([item["agreement"] for item in scored]) * min(len(scored) / 3.0, 1.0)) if scored else 0.0,
                "notes": [
                    "Agreement means the two modalities move in similar transition-support direction.",
                    "High agreement is not proof of correctness; it improves review confidence.",
                ],
            }
        )
    return {
        "analysis_status": "complete" if rows else "limited",
        "method": "deterministic_pairwise_modality_agreement_v1",
        "modality_pairs": pair_rows,
        "summary": {
            "pair_count": len(pair_rows),
            "mean_agreement_score": _distribution([row["agreement_score"] for row in pair_rows]).get("mean"),
            "strongest_pair": max(pair_rows, key=lambda row: (row["agreement_score"], row["modality_pair"])) if pair_rows else None,
            "weakest_pair": min(pair_rows, key=lambda row: (row["agreement_score"], row["modality_pair"])) if pair_rows else None,
        },
    }


def build_modality_disagreement(modality_agreement: dict) -> dict:
    pairs = []
    for row in modality_agreement.get("modality_pairs", []):
        copied = dict(row)
        copied["confidence"] = _clamp(row.get("disagreement_score", 0.0) * row.get("confidence", 0.0))
        copied["notes"] = [
            "Disagreement highlights where modalities do not support the same transition interpretation.",
            "Use this to prioritize human review, not automatic editing.",
        ]
        pairs.append(copied)
    return {
        "analysis_status": modality_agreement.get("analysis_status", "limited"),
        "method": "deterministic_pairwise_modality_disagreement_v1",
        "modality_pairs": sorted(pairs, key=lambda row: (-row["disagreement_score"], row["modality_pair"])),
        "summary": {
            "pair_count": len(pairs),
            "mean_disagreement_score": _distribution([row["disagreement_score"] for row in pairs]).get("mean"),
            "strongest_disagreement_pair": max(pairs, key=lambda row: (row["disagreement_score"], row["modality_pair"])) if pairs else None,
        },
    }


def write_consensus_outputs(bundle, consensus_outputs: dict) -> None:
    root = bundle.output_dir
    consensus_dir = root / "consensus"
    reports_dir = root / "reports"
    consensus_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)
    for filename, key in [
        ("evidence_consensus.json", "evidence_consensus"),
        ("modality_agreement.json", "modality_agreement"),
        ("modality_disagreement.json", "modality_disagreement"),
        ("transition_confidence.json", "transition_confidence"),
        ("evidence_score_summary.json", "evidence_score_summary"),
        ("false_positive_boundaries.json", "false_positive_boundaries"),
        ("continuity_analysis.json", "continuity_analysis"),
    ]:
        write_json(consensus_dir / filename, consensus_outputs[key])
    _write_reports(reports_dir, consensus_outputs)


def _write_reports(reports_dir: Path, consensus_outputs: dict) -> None:
    consensus = consensus_outputs["evidence_consensus"]
    continuity = consensus_outputs["continuity_analysis"]
    transition = consensus_outputs["transition_confidence"]
    payload = {
        "evidence_consensus": consensus.get("summary", {}),
        "modality_agreement": consensus_outputs["modality_agreement"].get("summary", {}),
        "modality_disagreement": consensus_outputs["modality_disagreement"].get("summary", {}),
        "evidence_score_summary": consensus_outputs["evidence_score_summary"],
    }
    write_json(reports_dir / "evidence_consensus_report.json", payload)
    write_json(reports_dir / "continuity_report.json", continuity)
    write_json(reports_dir / "segmentation_confidence_report.json", {
        "transition_confidence": transition,
        "false_positive_boundaries": consensus_outputs["false_positive_boundaries"],
    })
    (reports_dir / "evidence_consensus_report.md").write_text(_consensus_md(payload), encoding="utf-8")
    (reports_dir / "continuity_report.md").write_text(_continuity_md(continuity), encoding="utf-8")
    (reports_dir / "segmentation_confidence_report.md").write_text(_segmentation_md(transition, consensus_outputs["false_positive_boundaries"]), encoding="utf-8")


def _consensus_md(payload: dict) -> str:
    summary = payload["evidence_consensus"]
    scores = payload["evidence_score_summary"]
    lines = [
        "# Evidence Consensus Report",
        "",
        "Consensus outputs are deterministic evidence-fusion heuristics intended to improve explainability and editorial review. They are not semantic truth guarantees or autonomous editorial decisions.",
        "",
        f"- Consensus items: `{summary.get('consensus_item_count')}`",
        f"- Mean consensus score: `{(summary.get('consensus_score_distribution') or {}).get('mean')}`",
        f"- Mean false-positive probability: `{summary.get('mean_false_positive_probability')}`",
        f"- Overall evidence strength: `{scores.get('overall_evidence_strength')}`",
        "",
        "## Weakest Evidence",
        "",
    ]
    lines.extend(f"- `{row.get('modality')}`: `{row.get('score')}` ({row.get('class')})" for row in scores.get("weakest_evidence", []))
    return "\n".join(lines) + "\n"


def _continuity_md(continuity: dict) -> str:
    summary = continuity.get("summary", {})
    lines = [
        "# Continuity Report",
        "",
        "Continuity compares topic, rhetorical, emotional, pacing, and acoustic continuity across adjacent segments.",
        "",
        f"- Transitions: `{summary.get('transition_count')}`",
        f"- Mean topic continuity: `{summary.get('mean_topic_continuity')}`",
        f"- Mean rhetorical continuity: `{summary.get('mean_rhetorical_continuity')}`",
        f"- Mean cross-modal continuity agreement: `{summary.get('mean_cross_modal_continuity_agreement')}`",
    ]
    return "\n".join(lines) + "\n"


def _segmentation_md(transition: dict, false_positive: dict) -> str:
    summary = transition.get("summary", {})
    lines = [
        "# Segmentation Confidence Report",
        "",
        "Boundary confidence is deterministic review evidence. Boundaries are never removed automatically.",
        "",
        f"- Transitions: `{summary.get('transition_count')}`",
        f"- Likely true transitions: `{summary.get('likely_true_transition_count')}`",
        f"- Likely false positives: `{summary.get('likely_false_positive_count')}`",
        f"- False-positive boundary ratio: `{false_positive.get('false_positive_boundary_ratio')}`",
    ]
    return "\n".join(lines) + "\n"
