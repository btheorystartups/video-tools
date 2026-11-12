"""Deterministic boundary review diagnostics."""

from __future__ import annotations

from statistics import mean
from typing import Any

from stability import STATUS_COMPLETE, STATUS_LIMITED, deterministic_id


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def _pair_map(rows: list[dict], left: str = "from_segment_id", right: str = "to_segment_id") -> dict[tuple[str, str], dict]:
    return {(row.get(left), row.get(right)): row for row in rows}


def analyze_boundary_diagnostics(
    scene_segments: dict,
    audio_features: dict,
    acoustic_features: dict | None,
    topic_continuity: dict | None,
    rhetorical_coherence: dict | None,
    emotional_arc: dict | None,
    transition_confidence: dict | None = None,
    discourse_state: dict | None = None,
    argument_graph: dict | None = None,
    narrative_memory: dict | None = None,
    callback_resolution: dict | None = None,
    editorial_ambiguity: dict | None = None,
    visual_boundary_alignment: dict | None = None,
) -> dict:
    segments = scene_segments.get("segments") or []
    acoustic_features = acoustic_features or {}
    topic_continuity = topic_continuity or {}
    rhetorical_coherence = rhetorical_coherence or {}
    emotional_arc = emotional_arc or {}
    transition_confidence = transition_confidence or {}
    discourse_state = discourse_state or {}
    argument_graph = argument_graph or {}
    narrative_memory = narrative_memory or {}
    callback_resolution = callback_resolution or {}
    editorial_ambiguity = editorial_ambiguity or {}
    visual_boundary_alignment = visual_boundary_alignment or {}
    bridge = _pair_map(topic_continuity.get("topic_bridge_terms") or [])
    rhet = _pair_map(rhetorical_coherence.get("mode_transitions") or [])
    acoustic = _pair_map(acoustic_features.get("acoustic_contrast_between_segments") or [])
    transition = _pair_map(transition_confidence.get("transitions") or [])
    discourse = _pair_map(discourse_state.get("discourse_transitions") or [])
    ambiguity = _pair_map(editorial_ambiguity.get("ambiguity_regions") or [])
    visual_alignment = _pair_map(visual_boundary_alignment.get("boundaries") or [])
    callback_to = {}
    for row in callback_resolution.get("callback_pairs") or []:
        callback_to.setdefault(row.get("payoff_segment_id"), []).append(row)
    memory_to = {}
    for row in narrative_memory.get("callback_references") or []:
        memory_to.setdefault(row.get("to_segment_id"), []).append(row)
    unresolved_argument_segments = {
        segment_id
        for chain in argument_graph.get("unresolved_chains") or []
        for segment_id in chain.get("segment_ids", [])
    }
    arc = {row.get("segment_id"): row for row in emotional_arc.get("segments") or []}
    rows = []
    for index, (left, right) in enumerate(zip(segments, segments[1:]), start=1):
        pair = (left.get("segment_id"), right.get("segment_id"))
        gap = max(0.0, _num(right.get("start_sec")) - _num(left.get("end_sec")))
        pause_score = _clamp(gap / 2.0)
        sentence_score = 0.75 if str(left.get("text", "")).rstrip().endswith((".", "?", "!")) else 0.25
        topic_row = bridge.get(pair, {})
        topic_shift = _clamp(1.0 - _num(topic_row.get("continuity_score"), 0.5))
        rhet_row = rhet.get(pair, {})
        rhetorical_shift = 0.7 if rhet_row.get("transition_type") == "mode_shift" else 0.2 if rhet_row else 0.35
        acoustic_row = acoustic.get(pair, {})
        acoustic_shift = _clamp(_num(acoustic_row.get("energy_contrast"), 0.0) / max(_num((acoustic_features.get("rms_energy_summary") or {}).get("mean"), 0.001) * 1.4, 0.001)) if acoustic_row else 0.35
        pacing_shift = _clamp(abs(_num(right.get("speech_rate_wpm")) - _num(left.get("speech_rate_wpm"))) / 130.0)
        left_arc = arc.get(left.get("segment_id"), {})
        right_arc = arc.get(right.get("segment_id"), {})
        emotional_shift = _clamp(abs(_num(right_arc.get("intensity"), 0.5) - _num(left_arc.get("intensity"), 0.5)) + (0.18 if left_arc.get("dominant_tone") != right_arc.get("dominant_tone") and left_arc and right_arc else 0.0))
        support_scores = [pause_score, sentence_score, topic_shift, rhetorical_shift, acoustic_shift, pacing_shift, emotional_shift]
        support = _clamp(mean(support_scores))
        contradictions = sum(1 for value in support_scores if value <= 0.28)
        transition_row = transition.get(pair, {})
        discourse_row = discourse.get(pair, {})
        ambiguity_row = ambiguity.get(pair, {})
        visual_row = visual_alignment.get(pair, {})
        visual_shift = _clamp(_num(visual_row.get("visual_support"), 0.0)) if visual_row else 0.0
        if visual_row:
            support_scores.append(visual_shift)
            support = _clamp(mean(support_scores))
            contradictions = sum(1 for value in support_scores if value <= 0.28)
        callback_rows = callback_to.get(right.get("segment_id"), []) + memory_to.get(right.get("segment_id"), [])
        discourse_continuation = _clamp(_num(discourse_row.get("discourse_continuation_evidence"), 0.0))
        unresolved_carryover = _clamp(_num(discourse_row.get("unresolved_pressure_carryover"), 0.0))
        callback_carryover = _clamp(min(len(callback_rows) / 3.0, 1.0))
        narrative_carryover = _clamp(1.0 if memory_to.get(right.get("segment_id")) else 0.0)
        intentional_likelihood = _clamp(
            (0.28 if ambiguity_row.get("ambiguity_class") in {"callback_supported_drift", "rhetorical_pivot", "illustrative_detour", "likely_intentional_tangent"} else 0.0)
            + discourse_continuation * 0.28
            + callback_carryover * 0.22
            + (0.12 if rhet_row.get("transition_type") == "mode_shift" else 0.0)
            + narrative_carryover * 0.1
        )
        ambiguity_override = bool(ambiguity_row.get("ambiguity_class") in {"callback_supported_drift", "rhetorical_pivot", "illustrative_detour", "likely_intentional_tangent"} and intentional_likelihood >= 0.45)
        unresolved_argument = right.get("segment_id") in unresolved_argument_segments or left.get("segment_id") in unresolved_argument_segments
        likely_good = bool(support >= 0.56 and contradictions <= 2)
        likely_review = bool((not likely_good or contradictions >= 3 or transition_row.get("likely_false_positive") or unresolved_argument) and not ambiguity_override)
        boundary_class = "bad_boundary" if likely_review and support < 0.42 else "rhetorical_transition"
        if unresolved_argument:
            boundary_class = "unresolved_discourse_continuation"
        if ambiguity_override:
            boundary_class = "intentional_pivot" if ambiguity_row.get("ambiguity_class") == "rhetorical_pivot" else "intentional_tangent"
        elif callback_carryover:
            boundary_class = "delayed_payoff_transition"
        elif discourse_continuation >= 0.48:
            boundary_class = "thematic_continuation"
        action = "Accept as likely good boundary after transcript spot-check." if likely_good else "Review boundary manually; do not rewrite automatically."
        if ambiguity_override:
            action = "Review as possible intentional rhetorical movement; do not rewrite automatically."
        elif unresolved_argument:
            action = "Review unresolved argument carryover before treating this as a clean boundary."
        if sentence_score <= 0.3 and topic_shift >= 0.58:
            action = "Review boundary because sentence continuity conflicts with topic shift evidence."
        elif topic_shift <= 0.34 and acoustic_shift >= 0.58:
            action = "Review boundary because topic continuation conflicts with acoustic shift evidence."
        elif visual_row.get("visual_contradiction", 0) >= 0.45:
            action = "Review boundary because visual evidence conflicts with transcript/discourse boundary evidence."
        rows.append(
            {
                "boundary_id": deterministic_id("BND", left.get("segment_id"), right.get("segment_id"), left.get("end_sec"), right.get("start_sec")),
                "boundary_index": index,
                "from_segment_id": left.get("segment_id"),
                "to_segment_id": right.get("segment_id"),
                "transcript_pause_evidence": {"score": pause_score, "gap_sec": round(gap, 3)},
                "sentence_completion_evidence": {"score": sentence_score, "left_ends_sentence": sentence_score >= 0.7},
                "topic_shift_evidence": {"score": topic_shift, "bridge_terms": topic_row.get("bridge_terms", [])},
                "rhetorical_shift_evidence": {"score": _clamp(rhetorical_shift), "transition_type": rhet_row.get("transition_type")},
                "acoustic_shift_evidence": {"score": acoustic_shift},
                "pacing_shift_evidence": {"score": pacing_shift},
                "emotional_shift_evidence": {"score": emotional_shift},
                "visual_shift_evidence": {
                    "score": visual_shift,
                    "matched_shot_boundary_id": visual_row.get("matched_shot_boundary_id"),
                    "visual_contradiction": visual_row.get("visual_contradiction"),
                    "boundary_evidence_type": visual_row.get("boundary_evidence_type"),
                },
                "consensus_support": support,
                "contradiction_count": contradictions,
                "discourse_continuation_evidence": {"score": discourse_continuation, "carryover_concepts": discourse_row.get("carryover_concepts", [])},
                "unresolved_argument_carryover": unresolved_argument,
                "callback_carryover": {"score": callback_carryover, "callback_count": len(callback_rows)},
                "narrative_continuity_carryover": {"score": narrative_carryover},
                "ambiguity_override": ambiguity_override,
                "intentional_tangent_likelihood": intentional_likelihood,
                "boundary_interpretation": boundary_class,
                "likely_good_boundary": likely_good,
                "likely_review_boundary": likely_review,
                "suggested_human_review_action": action,
            }
        )
    return {
        "analysis_status": STATUS_COMPLETE if rows else STATUS_LIMITED,
        "method": "deterministic_boundary_diagnostics_v1",
        "boundaries": rows,
        "summary": {
            "boundary_count": len(rows),
            "likely_good_boundary_count": sum(1 for row in rows if row["likely_good_boundary"]),
            "likely_review_boundary_count": sum(1 for row in rows if row["likely_review_boundary"]),
            "mean_consensus_support": _clamp(mean([row["consensus_support"] for row in rows]) if rows else 0.0),
            "total_contradictions": sum(row["contradiction_count"] for row in rows),
        },
        "limitations": [
            "Boundary diagnostics are review evidence only.",
            "No segment boundary, media file, or timeline is modified.",
        ],
    }


def attach_boundary_diagnostics(scene_segments: dict, boundary_diagnostics: dict) -> dict:
    by_to = {row.get("to_segment_id"): row for row in boundary_diagnostics.get("boundaries", [])}
    copied = dict(scene_segments)
    copied["segments"] = []
    for segment in scene_segments.get("segments") or []:
        row = dict(segment)
        diagnostic = by_to.get(row.get("segment_id"))
        if diagnostic:
            row["boundary_diagnostic"] = {
                "boundary_id": diagnostic.get("boundary_id"),
                "consensus_support": diagnostic.get("consensus_support"),
                "contradiction_count": diagnostic.get("contradiction_count"),
                "likely_review_boundary": diagnostic.get("likely_review_boundary"),
                "suggested_human_review_action": diagnostic.get("suggested_human_review_action"),
            }
        copied["segments"].append(row)
    return copied
