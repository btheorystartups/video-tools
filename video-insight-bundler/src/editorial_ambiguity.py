"""Interpret low-continuity regions with deterministic editorial ambiguity classes."""

from __future__ import annotations

from statistics import mean

from stability import STATUS_COMPLETE, STATUS_LIMITED, deterministic_id


AMBIGUITY_CLASSES = {
    "likely_intentional_tangent",
    "rhetorical_pivot",
    "illustrative_detour",
    "unresolved_drift",
    "exploratory_abstraction",
    "callback_supported_drift",
    "unsupported_drift",
}


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def _by_pair(rows: list[dict], left: str = "from_segment_id", right: str = "to_segment_id") -> dict[tuple[str, str], dict]:
    return {(row.get(left), row.get(right)): row for row in rows}


def analyze_editorial_ambiguity(
    scene_segments: dict,
    topic_continuity: dict | None = None,
    rhetorical_coherence: dict | None = None,
    discourse_state: dict | None = None,
    argument_graph: dict | None = None,
    narrative_memory: dict | None = None,
    callback_resolution: dict | None = None,
) -> dict:
    segments = scene_segments.get("segments") or []
    if len(segments) < 2:
        return {
            "analysis_status": STATUS_LIMITED,
            "method": "deterministic_editorial_ambiguity_v1",
            "ambiguity_regions": [],
            "continuity_reinterpretation": [],
            "recommendation_impact": [],
            "ambiguity_confidence_score": 0.0,
            "limitations": ["At least two segments are required for ambiguity interpretation."],
        }

    topic_pairs = _by_pair((topic_continuity or {}).get("topic_bridge_terms", []))
    rhet_pairs = _by_pair((rhetorical_coherence or {}).get("mode_transitions", []))
    discourse_pairs = _by_pair((discourse_state or {}).get("discourse_transitions", []))
    callbacks_by_to = {}
    for row in (callback_resolution or {}).get("callback_pairs", []):
        callbacks_by_to.setdefault(row.get("payoff_segment_id"), []).append(row)
    returns_by_to = {}
    for row in (narrative_memory or {}).get("callback_references", []):
        returns_by_to.setdefault(row.get("to_segment_id"), []).append(row)
    unresolved_chain_segments = {
        segment_id
        for chain in (argument_graph or {}).get("unresolved_chains", [])
        for segment_id in chain.get("segment_ids", [])
    }

    regions = []
    reinterpretations = []
    impacts = []
    confidence_values = []
    for left, right in zip(segments, segments[1:]):
        pair = (left.get("segment_id"), right.get("segment_id"))
        topic = topic_pairs.get(pair, {})
        rhet = rhet_pairs.get(pair, {})
        disc = discourse_pairs.get(pair, {})
        topic_score = float(topic.get("continuity_score") if topic.get("continuity_score") is not None else 0.5)
        rhetorical_shift = rhet.get("transition_type") == "mode_shift"
        carryover = disc.get("carryover_concepts") or []
        callback_rows = callbacks_by_to.get(right.get("segment_id"), []) + returns_by_to.get(right.get("segment_id"), [])
        right_markers = set(right.get("topic_markers") or [])
        pressure = float(disc.get("unresolved_pressure_carryover") or 0.0)
        support_evidence = []
        conflict_evidence = []
        if carryover:
            support_evidence.append(f"carryover concepts: {', '.join(carryover[:6])}")
        if callback_rows:
            support_evidence.append(f"{len(callback_rows)} callback/reference row(s) point into this segment")
        if rhetorical_shift:
            support_evidence.append("rhetorical mode shift is explicit")
        if right_markers & {"example"}:
            support_evidence.append("right segment contains example marker")
        if topic_score < 0.34:
            conflict_evidence.append(f"low lexical continuity: {topic_score}")
        if pressure > 0.55:
            conflict_evidence.append(f"unresolved discourse pressure carryover: {pressure}")
        if right.get("segment_id") in unresolved_chain_segments:
            conflict_evidence.append("right segment participates in unresolved argument chain")

        if topic_score < 0.34 and callback_rows:
            klass = "callback_supported_drift"
        elif topic_score < 0.34 and right_markers & {"example"}:
            klass = "illustrative_detour"
        elif topic_score < 0.34 and rhetorical_shift and carryover:
            klass = "rhetorical_pivot"
        elif topic_score < 0.34 and pressure > 0.55:
            klass = "unresolved_drift"
        elif topic_score < 0.34 and not support_evidence:
            klass = "unsupported_drift"
        elif topic_score < 0.5 and any(term in (right.get("text") or "").lower() for term in ["why", "meaning", "principle", "truth"]):
            klass = "exploratory_abstraction"
        elif topic_score < 0.5:
            klass = "likely_intentional_tangent" if rhetorical_shift or callback_rows else "unsupported_drift"
        else:
            continue

        confidence = _clamp(
            0.25
            + (1.0 - topic_score) * 0.32
            + min(len(support_evidence), 3) * 0.12
            + min(len(conflict_evidence), 2) * 0.08
        )
        confidence_values.append(confidence)
        adjusted = topic_score
        if klass in {"callback_supported_drift", "rhetorical_pivot", "illustrative_detour", "likely_intentional_tangent"}:
            adjusted = _clamp(topic_score + 0.18 + min(len(support_evidence), 2) * 0.06)
        if klass in {"unresolved_drift", "unsupported_drift"}:
            adjusted = _clamp(topic_score - 0.08)
        region = {
            "ambiguity_id": deterministic_id("AMB", left.get("segment_id"), right.get("segment_id"), klass),
            "from_segment_id": left.get("segment_id"),
            "to_segment_id": right.get("segment_id"),
            "ambiguity_class": klass,
            "supporting_evidence": support_evidence,
            "conflicting_evidence": conflict_evidence,
            "ambiguity_confidence": confidence,
            "continuity_reinterpretation": {
                "original_topic_continuity": _clamp(topic_score),
                "ambiguity_adjusted_continuity": adjusted,
                "interpretation": _interpretation(klass),
            },
            "recommendation_impact": _impact(klass, left.get("segment_id"), right.get("segment_id")),
        }
        regions.append(region)
        reinterpretations.append(region["continuity_reinterpretation"] | {"ambiguity_id": region["ambiguity_id"]})
        impacts.append(region["recommendation_impact"] | {"ambiguity_id": region["ambiguity_id"]})

    class_counts: dict[str, int] = {}
    for row in regions:
        class_counts[row["ambiguity_class"]] = class_counts.get(row["ambiguity_class"], 0) + 1
    return {
        "analysis_status": STATUS_COMPLETE if regions else STATUS_LIMITED,
        "method": "deterministic_editorial_ambiguity_v1",
        "ambiguity_regions": regions,
        "ambiguity_class_counts": dict(sorted(class_counts.items())),
        "continuity_reinterpretation": reinterpretations,
        "recommendation_impact": impacts,
        "ambiguity_confidence_score": _clamp(mean(confidence_values) if confidence_values else 0.0),
        "limitations": [
            "Ambiguity classes are deterministic editorial-review interpretations.",
            "They are not intent detection, psychological inference, or semantic truth guarantees.",
        ],
    }


def _interpretation(klass: str) -> str:
    return {
        "callback_supported_drift": "Low lexical continuity is partly offset by callback evidence.",
        "rhetorical_pivot": "Low lexical continuity may be an explicit rhetorical transition.",
        "illustrative_detour": "Low lexical continuity may reflect an example or concrete detour.",
        "likely_intentional_tangent": "Low continuity has enough discourse support to review as intentional style.",
        "exploratory_abstraction": "Abstract framing may lower lexical continuity while preserving exploratory flow.",
        "unresolved_drift": "Low continuity carries unresolved pressure and should be reviewed as a gap.",
        "unsupported_drift": "Low continuity has weak support and should be reviewed as possible incoherence.",
    }.get(klass, "Ambiguity requires human review.")


def _impact(klass: str, from_segment_id: str | None, to_segment_id: str | None) -> dict:
    if klass in {"unresolved_drift", "unsupported_drift"}:
        action = f"Bridge or resolve drift between segments {from_segment_id} and {to_segment_id}."
        confidence_delta = "increase_recommendation_confidence"
    elif klass == "callback_supported_drift":
        action = f"Keep possible drift between {from_segment_id} and {to_segment_id} under callback review before recommending a cut."
        confidence_delta = "reduce_cut_confidence"
    elif klass == "illustrative_detour":
        action = f"Clarify example purpose around segment {to_segment_id} if the detour feels unsupported."
        confidence_delta = "shift_to_clarification"
    else:
        action = f"Review transition {from_segment_id}->{to_segment_id} as a possible intentional rhetorical move."
        confidence_delta = "preserve_ambiguity"
    return {
        "impact_class": confidence_delta,
        "suggested_review_action": action,
    }


def build_discourse_summary(
    scene_segments: dict,
    topic_continuity: dict | None = None,
    rhetorical_coherence: dict | None = None,
    discourse_state: dict | None = None,
    argument_graph: dict | None = None,
    narrative_memory: dict | None = None,
    callback_resolution: dict | None = None,
    editorial_ambiguity: dict | None = None,
    audio_features: dict | None = None,
    emotional_arc: dict | None = None,
) -> dict:
    segments = scene_segments.get("segments") or []
    topic_score = float((topic_continuity or {}).get("topic_continuity_score") or 0.0)
    rhetorical_score = float((rhetorical_coherence or {}).get("rhetorical_coherence_score") or 0.0)
    argument_score = float((argument_graph or {}).get("argument_completeness_score") or 0.0)
    callback_score = float((callback_resolution or {}).get("callback_strength_score") or 0.0)
    thematic_score = float((narrative_memory or {}).get("thematic_persistence_score") or 0.0)
    narrative_score = _clamp((thematic_score * 0.45) + float((narrative_memory or {}).get("narrative_recovery_score") or 0.0) * 0.35 + (1.0 - float((narrative_memory or {}).get("narrative_drift_score") or 0.0)) * 0.2)
    rates = [float(row.get("speech_rate_wpm") or 0.0) for row in segments]
    if len(rates) > 1:
        pacing_score = _clamp(1.0 - (max(rates) - min(rates)) / 220.0)
    else:
        pacing_score = 0.5 if rates else 0.0
    emotional_rows = (emotional_arc or {}).get("segments") or []
    intensities = [float(row.get("intensity") or 0.0) for row in emotional_rows]
    emotional_score = _clamp(1.0 - (max(intensities) - min(intensities)) if len(intensities) > 1 else (0.5 if intensities else 0.0))
    discourse_score = float((discourse_state or {}).get("discourse_continuity_score") or 0.0)
    decomposed = {
        "lexical_continuity": _clamp(topic_score),
        "rhetorical_continuity": _clamp(rhetorical_score),
        "argument_continuity": _clamp(argument_score),
        "callback_continuity": _clamp(callback_score),
        "thematic_persistence": _clamp(thematic_score),
        "narrative_continuity": narrative_score,
        "pacing_continuity": pacing_score,
        "emotional_continuity": emotional_score,
        "discourse_state_continuity": _clamp(discourse_score),
    }
    contradiction_penalty = min(len((argument_graph or {}).get("contradiction_clusters", [])) * 0.04, 0.24)
    ambiguity_regions = (editorial_ambiguity or {}).get("ambiguity_regions", [])
    ambiguity_boost = min(
        sum(0.04 for row in ambiguity_regions if row.get("ambiguity_class") in {"callback_supported_drift", "rhetorical_pivot", "illustrative_detour", "likely_intentional_tangent"}),
        0.18,
    )
    base = mean(decomposed.values()) if decomposed else 0.0
    contradiction_adjusted = _clamp(base - contradiction_penalty)
    ambiguity_adjusted = _clamp(contradiction_adjusted + ambiguity_boost - min(sum(0.04 for row in ambiguity_regions if row.get("ambiguity_class") in {"unresolved_drift", "unsupported_drift"}), 0.16))
    strongest = sorted(decomposed.items(), key=lambda item: (-item[1], item[0]))[:3]
    weakest = sorted(decomposed.items(), key=lambda item: (item[1], item[0]))[:3]
    return {
        "analysis_status": STATUS_COMPLETE if segments else STATUS_LIMITED,
        "method": "deterministic_continuity_decomposition_v1",
        "decomposed_scores": decomposed,
        "strongest_continuity_dimensions": [{"dimension": key, "score": value} for key, value in strongest],
        "weakest_continuity_dimensions": [{"dimension": key, "score": value} for key, value in weakest],
        "contradiction_adjusted_continuity": contradiction_adjusted,
        "ambiguity_adjusted_continuity": ambiguity_adjusted,
        "narrative_recovery_score": _clamp(float((narrative_memory or {}).get("narrative_recovery_score") or 0.0)),
        "unresolved_discourse_pressure": _clamp(float((discourse_state or {}).get("discourse_pressure_score") or 0.0)),
        "argument_completeness_score": _clamp(argument_score),
        "callback_resolution_quality": _clamp(float((callback_resolution or {}).get("payoff_quality_score") or 0.0)),
        "ambiguity_summary": {
            "ambiguity_region_count": len(ambiguity_regions),
            "class_counts": (editorial_ambiguity or {}).get("ambiguity_class_counts", {}),
            "confidence": (editorial_ambiguity or {}).get("ambiguity_confidence_score"),
        },
        "limitations": [
            "Continuity decomposition is deterministic editorial evidence for human review.",
            "It does not make semantic truth, intent, or autonomous edit claims.",
        ],
    }
