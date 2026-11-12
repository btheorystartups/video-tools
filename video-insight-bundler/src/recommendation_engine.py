"""Evidence-ranked recommendation generation."""

from __future__ import annotations


def _top_category(profile: dict) -> str:
    categories = profile.get("top_categories") or []
    if not categories:
        return "undetermined"
    first = categories[0]
    return f"{first.get('label')} ({first.get('weight')})"


def _time_range(segment: dict) -> dict:
    return {"start_sec": segment.get("start_sec"), "end_sec": segment.get("end_sec")}


def _rec(
    issue_type: str,
    severity: str,
    confidence: float,
    segments: list[dict],
    evidence: list[str],
    why: str,
    edit: str,
    benefit: str,
    metrics: dict,
) -> dict:
    return {
        "issue_type": issue_type,
        "severity": severity,
        "confidence": round(float(confidence), 3),
        "affected_segment_ids": [segment.get("segment_id") for segment in segments if segment.get("segment_id")],
        "timestamp_range": {
            "start_sec": min((segment.get("start_sec") for segment in segments if segment.get("start_sec") is not None), default=None),
            "end_sec": max((segment.get("end_sec") for segment in segments if segment.get("end_sec") is not None), default=None),
        },
        "evidence": evidence,
        "why_it_matters": why,
        "suggested_edit": edit,
        "expected_benefit": benefit,
        "supporting_metrics": metrics,
    }


def build_recommendation_outputs(
    media_metadata: dict,
    transcript: dict,
    audio_features: dict,
    scene_segments: dict,
    emotional_arc: dict,
    persona_profile: dict,
    teaching_profile: dict,
    acoustic_features: dict | None = None,
    topic_analysis: dict | None = None,
    rhetorical_analysis: dict | None = None,
    topic_continuity: dict | None = None,
    rhetorical_coherence: dict | None = None,
) -> dict:
    wpm = audio_features.get("overall_words_per_minute")
    pause_count = audio_features.get("pause_count", 0)
    transcript_status = transcript.get("transcription_status")
    segments = scene_segments.get("segments") or []
    acoustic_features = acoustic_features or {}
    topic_analysis = topic_analysis or {}
    rhetorical_analysis = rhetorical_analysis or {}
    topic_continuity = topic_continuity or {}
    rhetorical_coherence = rhetorical_coherence or {}
    recommendations: list[dict] = []

    if transcript_status != "complete":
        recommendations.append(
            _rec(
                "clarity",
                "high",
                0.9,
                segments[:1],
                [f"Transcript status is {transcript_status}."],
                "Most language, pacing, topic, and rhetorical guidance depends on transcript evidence.",
                "Provide a transcript import or enable local faster-whisper transcription before making final editorial decisions.",
                "Improves reliability of segment-specific review.",
                {"transcription_status": transcript_status},
            )
        )

    if wpm and (wpm > 180 or wpm < 95):
        recommendations.append(
            _rec(
                "pacing",
                "medium" if 80 <= wpm <= 210 else "high",
                0.74,
                segments,
                [f"Overall speech rate is {wpm} WPM."],
                "Very fast or very slow delivery can reduce comprehension or perceived momentum.",
                "Adjust cuts, pauses, or visual support around dense claims.",
                "Creates a more legible explanatory rhythm.",
                {"overall_words_per_minute": wpm, "pause_count": pause_count},
            )
        )

    questionable = [segment for segment in segments if (segment.get("boundary") or {}).get("questionable")]
    if questionable:
        recommendations.append(
            _rec(
                "segment_transitions",
                "medium",
                0.68,
                questionable[:5],
                [f"{len(questionable)} segment boundary/boundaries were flagged as questionable."],
                "Weak boundaries make downstream analysis and human editing less precise.",
                "Review the flagged boundaries and align cuts with sentence ends, pauses, or explicit signposts.",
                "Improves structure and segment-level interpretability.",
                {"questionable_boundary_count": len(questionable)},
            )
        )

    drift = topic_analysis.get("topic_drift_score")
    if drift is not None and drift > 0.7:
        shift_segments = []
        ids = {item.get("to_segment_id") for item in topic_analysis.get("likely_topic_shifts", [])[:4]}
        shift_segments = [segment for segment in segments if segment.get("segment_id") in ids]
        recommendations.append(
            _rec(
                "topic_continuity",
                "medium",
                0.7,
                shift_segments,
                [f"Topic drift score is {drift}."],
                "Abrupt topic shifts can feel unsupported without a transition sentence or visual reset.",
                "Add signposting before high-shift segments and restate the through-line after the shift.",
                "Makes the argument easier to follow.",
                {"topic_drift_score": drift},
            )
        )

    for shift in (topic_continuity.get("unsupported_topic_shifts") or [])[:4]:
        from_id = shift.get("from_segment_id")
        to_id = shift.get("to_segment_id")
        shift_segments = [segment for segment in segments if segment.get("segment_id") in {from_id, to_id}]
        recommendations.append(
            _rec(
                "topic_continuity_issue",
                "medium",
                0.72,
                shift_segments,
                [f"Unsupported topic shift from {from_id} to {to_id}; continuity score {shift.get('continuity_score')}."],
                "A topic jump without bridge terms can make the argument feel disconnected.",
                f"Add bridge sentence between segment {from_id} and {to_id}.",
                "Improves continuity while preserving human control over edits.",
                {"topic_continuity_score": topic_continuity.get("topic_continuity_score"), "unsupported_shift": shift},
            )
        )

    silence_ratio = acoustic_features.get("silence_ratio")
    if silence_ratio is not None and silence_ratio > 0.42:
        recommendations.append(
            _rec(
                "acoustic_energy",
                "low",
                0.58,
                segments,
                [f"Approximate silence ratio is {silence_ratio}."],
                "Long low-energy stretches may be intentional, but they deserve review against pacing and edit goals.",
                "Review long silent regions and decide whether to tighten, emphasize, or support them visually.",
                "Helps distinguish intentional pauses from momentum loss.",
                {"silence_ratio": silence_ratio},
            )
        )

    balance = rhetorical_analysis.get("rhetorical_balance_score")
    if balance is not None and balance < 0.35:
        recommendations.append(
            _rec(
                "rhetorical_flow",
                "medium",
                0.65,
                segments,
                [f"Rhetorical balance score is {balance}."],
                "A large imbalance between claims/examples or abstract/actionable language can make the argument harder to apply.",
                "Pair abstract claims with concrete examples or steps; pair examples with a clear takeaway.",
                "Improves clarity and audience retention.",
                {"rhetorical_balance_score": balance},
            )
        )

    for question in (rhetorical_coherence.get("unresolved_questions") or [])[:4]:
        segment_id = question.get("segment_id")
        rec_segments = [segment for segment in segments if segment.get("segment_id") == segment_id]
        recommendations.append(
            _rec(
                "rhetorical_coherence_issue",
                "medium",
                0.69,
                rec_segments,
                [f"Unresolved question detected in segment {segment_id}."],
                "Questions that are introduced but not answered can weaken the explanatory through-line.",
                f"Resolve question introduced in segment {segment_id}.",
                "Makes the rhetorical promise clearer for viewers.",
                {"rhetorical_coherence_score": rhetorical_coherence.get("rhetorical_coherence_score"), "issue": question},
            )
        )

    for claim in (rhetorical_coherence.get("claims_without_examples") or [])[:4]:
        segment_id = claim.get("segment_id")
        rec_segments = [segment for segment in segments if segment.get("segment_id") == segment_id]
        recommendations.append(
            _rec(
                "claim_example_balance",
                "medium",
                0.66,
                rec_segments,
                [f"Claim without nearby example in segment {segment_id}."],
                "Unsupported claims can feel abstract or hard to apply.",
                f"Pair claim in segment {segment_id} with a concrete example.",
                "Improves clarity and practical uptake.",
                {"rhetorical_coherence_score": rhetorical_coherence.get("rhetorical_coherence_score"), "issue": claim},
            )
        )

    if segments:
        opening = segments[0]
        closing = segments[-1]
        if opening.get("word_count", 0) < 18:
            recommendations.append(
                _rec(
                    "opening_strength",
                    "low",
                    0.54,
                    [opening],
                    [f"Opening segment has {opening.get('word_count')} transcript words."],
                    "A thin opening may not establish the premise before the video moves on.",
                    "Make the opening promise explicit: problem, stakes, and payoff.",
                    "Gives viewers a clearer reason to continue.",
                    {"opening_word_count": opening.get("word_count")},
                )
            )
        if closing.get("word_count", 0) < 18 and len(segments) > 1:
            recommendations.append(
                _rec(
                    "opening_closing_strength",
                    "low",
                    0.52,
                    [closing],
                    [f"Closing segment has {closing.get('word_count')} transcript words."],
                    "A short closing may leave the takeaway implicit.",
                    "End with the core takeaway and a concrete next thought or action.",
                    "Improves memorability and completion impact.",
                    {"closing_word_count": closing.get("word_count")},
                )
            )

    recommendations = sorted(recommendations, key=lambda item: (-{"high": 3, "medium": 2, "low": 1}.get(item["severity"], 0), -item["confidence"], item["issue_type"]))
    lines = [
        "# Recommendations",
        "",
        "These recommendations are generated from local metadata, transcript timing when available, and transparent heuristics.",
        "",
        "## General",
        "",
        f"- Primary observed persona/style: {_top_category(persona_profile)}.",
        f"- Primary teaching/communication style: {_top_category(teaching_profile)}.",
        f"- Transcript status: `{transcript_status}`.",
    ]

    if transcript_status != "complete":
        lines.extend(
            [
                "- Install `faster-whisper` or provide an external transcript to unlock stronger topic, rhetorical, and pacing analysis.",
                "- Treat current segment and emotional arc results as timing-only or metadata-only scaffolding.",
            ]
        )

    lines.extend(["", "## Pacing", ""])
    if wpm:
        if wpm > 180:
            lines.append(f"- Speech rate is high at about {wpm} WPM. Add short pauses after dense claims and before transitions.")
        elif wpm < 95:
            lines.append(f"- Speech rate is slow at about {wpm} WPM. Tighten pauses or add visual changes to preserve momentum.")
        else:
            lines.append(f"- Speech rate is in a typical explanatory range at about {wpm} WPM.")
    else:
        lines.append("- Speech rate could not be measured without transcript timestamps.")
    if pause_count:
        lines.append(f"- Detected {pause_count} transcript-timed pauses. Review long pauses for intentional emphasis versus drift.")

    lines.extend(["", "## Clarity", ""])
    segment_count = scene_segments.get("segment_count", 0)
    lines.append(f"- The current pass found {segment_count} segments. Give each segment a clear claim, example, and transition.")
    lines.append("- Add explicit signposts around topic changes: problem, principle, example, implication, action.")

    lines.extend(["", "## Emotional Arc", ""])
    tones = [segment.get("dominant_tone") for segment in emotional_arc.get("segments", [])]
    if tones:
        dominant = max(set(tones), key=tones.count)
        lines.append(f"- Dominant inferred tone is `{dominant}`. Check whether that matches the intended audience effect.")
        if len(set(tones)) <= 1 and len(tones) > 2:
            lines.append("- Tonal variety appears low. Consider adding contrast: tension, example, resolution, or call to action.")
    else:
        lines.append("- Emotional arc could not be meaningfully inferred without segment text.")

    lines.extend(["", "## Segment-Specific Notes", ""])
    for segment in segments[:12]:
        lines.append(
            f"- `{segment.get('segment_id')}` {segment.get('start_sec')}s-{segment.get('end_sec')}s: "
            f"review the segment promise and transition. Summary: {segment.get('summary') or '[no transcript text]'}"
        )

    lines.extend(["", "## Evidence-Ranked Recommendations", ""])
    if recommendations:
        for item in recommendations[:12]:
            lines.append(
                f"- `{item['issue_type']}` ({item['severity']}, confidence {item['confidence']}): "
                f"{item['suggested_edit']} Evidence: {'; '.join(item['evidence'])}"
            )
    else:
        lines.append("- No high-priority heuristic recommendations were produced.")

    lines.extend(["", "## Human Review Checklist", ""])
    lines.append("- Verify transcript accuracy before using recommendations for editing decisions.")
    lines.append("- Compare sampled frames against actual cut points; this scaffold does not perform shot-boundary detection.")
    lines.append("- Treat persona/style labels as communication observations only.")
    return {
        "recommendation_status": "complete",
        "method": "deterministic_evidence_ranked_editorial_heuristics",
        "recommendations": recommendations,
        "limitations": [
            "Recommendations are grounded in available local evidence and should be reviewed by a human editor.",
            "They do not infer psychological state, identity, intent, or clinical traits.",
        ],
        "markdown": "\n".join(lines) + "\n",
    }


def build_recommendations(*args, **kwargs) -> str:
    return build_recommendation_outputs(*args, **kwargs)["markdown"]


def enrich_recommendations_with_consensus(recommendation_outputs: dict, consensus_outputs: dict) -> dict:
    """Attach consensus grounding to proposal-only recommendations."""

    outputs = dict(recommendation_outputs or {})
    recommendations = [dict(row) for row in outputs.get("recommendations", [])]
    consensus = consensus_outputs.get("evidence_consensus", {})
    consensus_items = consensus.get("consensus_items") or []
    by_segment: dict[str, list[dict]] = {}
    for item in consensus_items:
        for key in (item.get("from_segment_id"), item.get("to_segment_id"), item.get("segment_id")):
            if key:
                by_segment.setdefault(key, []).append(item)
    agreement_summary = (consensus_outputs.get("modality_agreement") or {}).get("summary", {})
    continuity_rows = {
        row.get("transition_id"): row
        for row in (consensus_outputs.get("continuity_analysis") or {}).get("continuity_rows", [])
    }

    enriched = []
    for rec in recommendations:
        linked = []
        for segment_id in rec.get("affected_segment_ids") or []:
            linked.extend(by_segment.get(segment_id, []))
        unique = {item.get("transition_id"): item for item in linked if item.get("transition_id")}
        linked = list(unique.values())
        if linked:
            consensus_score = round(sum(float(item.get("consensus_score") or 0.0) for item in linked) / len(linked), 3)
            false_positive_risk = round(max(float(item.get("false_positive_probability") or 0.0) for item in linked), 3)
            conflicting = sorted({modality for item in linked for modality in item.get("conflicting_modalities", [])})
            continuity_impact = round(sum(float(item.get("continuity_confidence") or 0.0) for item in linked) / len(linked), 3)
        else:
            consensus_score = (consensus.get("summary", {}).get("consensus_score_distribution") or {}).get("mean")
            false_positive_risk = consensus.get("summary", {}).get("mean_false_positive_probability")
            conflicting = []
            continuity_impact = None
        downgrade_reasons = []
        confidence = float(rec.get("confidence") or 0.0)
        if consensus_score is not None and consensus_score < 0.48:
            confidence = min(confidence, round(confidence * 0.82, 3))
            downgrade_reasons.append("low consensus backing")
        if false_positive_risk is not None and false_positive_risk >= 0.58:
            confidence = min(confidence, round(confidence * 0.86, 3))
            downgrade_reasons.append("false-positive transition risk")
        if conflicting:
            confidence = min(confidence, round(confidence * 0.92, 3))
            downgrade_reasons.append("conflicting modality evidence")
        rec["confidence"] = round(confidence, 3)
        rec["consensus_backing"] = {
            "consensus_score": consensus_score,
            "linked_transition_ids": sorted(unique) if linked else [],
            "modality_agreement_strength": agreement_summary.get("mean_agreement_score"),
            "conflicting_evidence_warnings": conflicting,
            "continuity_impact": continuity_impact,
            "false_positive_risk": false_positive_risk,
            "confidence_downgrade_reason": downgrade_reasons,
            "evidence_confidence": "strong" if consensus_score is not None and consensus_score >= 0.72 else "moderate" if consensus_score is not None and consensus_score >= 0.52 else "weak",
        }
        rec.setdefault("evidence", []).append(
            f"Consensus backing score: {consensus_score}; false-positive risk: {false_positive_risk}."
        )
        enriched.append(rec)

    outputs["recommendations"] = sorted(enriched, key=lambda item: (-{"high": 3, "medium": 2, "low": 1}.get(item.get("severity"), 0), -float(item.get("confidence") or 0.0), item.get("issue_type", "")))
    outputs["consensus_grounding"] = {
        "consensus_summary": consensus.get("summary", {}),
        "modality_agreement_summary": agreement_summary,
        "continuity_summary": (consensus_outputs.get("continuity_analysis") or {}).get("summary", {}),
        "false_positive_summary": (consensus_outputs.get("false_positive_boundaries") or {}),
        "limitations": [
            "Consensus grounding downgrades confidence when local evidence is weak or conflicting.",
            "Recommendations remain proposal-only editorial review notes.",
        ],
    }
    outputs["markdown"] = _markdown_with_consensus(outputs)
    return outputs


def enrich_recommendations_with_discourse(recommendation_outputs: dict, bundle) -> dict:
    """Add Phase 12 discourse-specific proposal notes without mutating source media."""

    outputs = dict(recommendation_outputs or {})
    recommendations = [dict(row) for row in outputs.get("recommendations", [])]
    segments = {row.get("segment_id"): row for row in (bundle.scene_segments.get("segments") or [])}
    discourse_state = getattr(bundle, "discourse_state", None) or {}
    argument_graph = getattr(bundle, "argument_graph", None) or {}
    callback_resolution = getattr(bundle, "callback_resolution", None) or {}
    editorial_ambiguity = getattr(bundle, "editorial_ambiguity", None) or {}
    discourse_summary = getattr(bundle, "discourse_summary", None) or {}

    for item in (discourse_state.get("unresolved_discourse_items") or [])[:5]:
        segment_id = item.get("segment_id")
        recommendations.append(
            _rec(
                "unresolved_discourse_state",
                "medium",
                0.72,
                [segments.get(segment_id, {})],
                [f"{item.get('item_type')} remains open from segment {segment_id}; concept {item.get('concept')}."],
                "Open discourse items increase pressure across transitions and can make continuity feel less realistic.",
                f"Resolve {item.get('item_type')} introduced in segment {segment_id}.",
                "Reduces unresolved discourse pressure before later transitions.",
                {"discourse_pressure_score": discourse_state.get("discourse_pressure_score"), "item": item},
            )
        )

    for chain in (argument_graph.get("unresolved_chains") or [])[:5]:
        segment_ids = chain.get("segment_ids") or []
        recommendations.append(
            _rec(
                "unresolved_argument_chain",
                "medium",
                0.74,
                [segments.get(segment_id, {}) for segment_id in segment_ids],
                [f"Argument chain {chain.get('chain_id')} is {chain.get('chain_status')} across segments {', '.join(segment_ids)}."],
                "A claim/support chain that remains partial or abandoned can read as contradiction or drift.",
                f"Resolve deferred claim introduced in segment {segment_ids[0] if segment_ids else chain.get('root_node_id')}.",
                "Improves argument completeness and release-readiness explainability.",
                {"argument_completeness_score": argument_graph.get("argument_completeness_score"), "chain": chain},
            )
        )

    for setup in (callback_resolution.get("unresolved_setups") or [])[:5]:
        segment_id = setup.get("setup_segment_id")
        recommendations.append(
            _rec(
                "unresolved_setup_payoff",
                "medium",
                0.73,
                [segments.get(segment_id, {})],
                [f"Unresolved {setup.get('setup_type')} introduced in segment {segment_id}."],
                "A setup without payoff weakens callback recognition and narrative memory.",
                f"Add payoff for setup introduced in segment {segment_id}.",
                "Improves callback resolution quality and continuity realism.",
                {"callback_strength_score": callback_resolution.get("callback_strength_score"), "setup": setup},
            )
        )

    for region in (editorial_ambiguity.get("ambiguity_regions") or [])[:5]:
        klass = region.get("ambiguity_class")
        if klass in {"unsupported_drift", "unresolved_drift"}:
            edit = f"Bridge rhetorical pivot between segments {region.get('from_segment_id')} and {region.get('to_segment_id')}."
        elif klass == "illustrative_detour":
            edit = f"Convert abstract framing near segment {region.get('to_segment_id')} into a clearer concrete example."
        elif klass == "callback_supported_drift":
            edit = f"Resolve callback introduced before segment {region.get('to_segment_id')} before the conclusion."
        else:
            edit = f"Review transition {region.get('from_segment_id')}->{region.get('to_segment_id')} as intentional drift before recommending a cut."
        recommendations.append(
            _rec(
                "editorial_ambiguity",
                "low" if klass not in {"unsupported_drift", "unresolved_drift"} else "medium",
                0.68,
                [segments.get(region.get("from_segment_id"), {}), segments.get(region.get("to_segment_id"), {})],
                [
                    f"Ambiguity class {klass}; supporting evidence: {'; '.join(region.get('supporting_evidence') or [])}; conflicting evidence: {'; '.join(region.get('conflicting_evidence') or [])}."
                ],
                "Low continuity may reflect either incoherence or intentional rhetorical style; the recommendation should preserve that ambiguity.",
                edit,
                "Improves recommendation specificity without making an intent claim.",
                {"ambiguity_adjusted_continuity": discourse_summary.get("ambiguity_adjusted_continuity"), "region": region},
            )
        )

    outputs["recommendations"] = sorted(
        recommendations,
        key=lambda item: (-{"high": 3, "medium": 2, "low": 1}.get(item.get("severity"), 0), -float(item.get("confidence") or 0.0), item.get("issue_type", "")),
    )
    outputs["discourse_grounding"] = {
        "discourse_summary": discourse_summary,
        "argument_completeness_score": argument_graph.get("argument_completeness_score"),
        "callback_resolution_quality": callback_resolution.get("payoff_quality_score"),
        "ambiguity_confidence_score": editorial_ambiguity.get("ambiguity_confidence_score"),
        "limitations": [
            "Discourse-grounded recommendations remain proposal-only review notes.",
            "They do not infer intent or apply edits.",
        ],
    }
    outputs["markdown"] = _markdown_with_consensus(outputs)
    return outputs


def enrich_recommendations_with_visual(recommendation_outputs: dict, bundle) -> dict:
    """Add deterministic visual-structure review proposals."""

    outputs = dict(recommendation_outputs or {})
    recommendations = [dict(row) for row in outputs.get("recommendations", [])]
    segments = {row.get("segment_id"): row for row in (bundle.scene_segments.get("segments") or [])}
    alignment = getattr(bundle, "visual_boundary_alignment", None) or {}
    continuity = getattr(bundle, "visual_continuity", None) or {}
    composition = getattr(bundle, "composition_features", None) or {}

    for row in (alignment.get("boundaries") or [])[:8]:
        from_id = row.get("from_segment_id")
        to_id = row.get("to_segment_id")
        if row.get("likely_nonvisual_boundary"):
            issue = "visual_boundary_alignment"
            edit = f"Add visual reset near boundary {from_id}->{to_id} only if human review confirms the discourse transition needs visible support."
            why = "The boundary is supported by transcript/rhetorical/discourse evidence but has weak visual reset evidence."
            severity = "medium"
        elif row.get("boundary_evidence_type") == "visual_reset_without_transcript_transition":
            issue = "unsupported_visual_jump"
            edit = f"Review abrupt visual change at {row.get('matched_shot_timestamp_sec')}s before treating it as a structural transition."
            why = "A visual transition occurs without matching discourse or transcript transition evidence."
            severity = "medium"
        elif row.get("visual_contradiction", 0) >= 0.45:
            issue = "visual_contradiction"
            edit = f"Review boundary {from_id}->{to_id}; visual evidence disagrees with nonvisual boundary evidence."
            why = "Visual contradiction pressure can reduce release readiness if not explained or adjusted."
            severity = "medium"
        else:
            continue
        rec = _rec(
            issue,
            severity,
            max(0.5, min(0.82, row.get("combined_boundary_confidence") or 0.55)),
            [segments.get(from_id, {}), segments.get(to_id, {})],
            [
                f"Visual support {row.get('visual_support')}; transcript {row.get('transcript_support')}; rhetorical {row.get('rhetorical_support')}; discourse {row.get('discourse_support')}; acoustic {row.get('acoustic_support')}.",
                f"Visual contradiction {row.get('visual_contradiction')}; evidence type {row.get('boundary_evidence_type')}.",
            ],
            why,
            edit,
            "Improves visual continuity explainability while preserving proposal-only safety.",
            {"visual_alignment": row},
        )
        rec["affected_boundary_ids"] = [row.get("alignment_id")]
        rec["visual_evidence"] = row.get("visual_evidence", {})
        rec["review_action"] = row.get("suggested_review_action")
        rec["limitations"] = row.get("limitations", [])
        recommendations.append(rec)

    for jump in (alignment.get("unsupported_visual_jumps") or [])[:5]:
        rec = _rec(
            "unsupported_visual_jump",
            "medium",
            max(0.52, min(0.82, jump.get("boundary_confidence") or 0.58)),
            [],
            [f"Shot boundary {jump.get('shot_boundary_id')} at {jump.get('timestamp_sec')}s has visual change score {jump.get('visual_change_score')} without nearby transcript/discourse boundary."],
            "Abrupt visual change without a discourse transition may distract from the argument or indicate an unmodeled edit point.",
            f"Review abrupt visual change at timestamp {jump.get('timestamp_sec')}s.",
            "Separates visual-only transitions from transcript or discourse boundaries.",
            {"unsupported_visual_jump": jump},
        )
        rec["affected_boundary_ids"] = [jump.get("shot_boundary_id")]
        rec["visual_evidence"] = jump
        rec["review_action"] = jump.get("suggested_review_action")
        rec["limitations"] = ["Visual-only jump evidence is local pixel/color/edge evidence, not a semantic claim."]
        recommendations.append(rec)

    dense_segments = [
        row
        for row in (composition.get("segment_summaries") or [])
        if (row.get("visual_energy") or 0) >= 0.68 or (row.get("mean_complexity") or 0) >= 0.7
    ]
    for row in dense_segments[:4]:
        segment = segments.get(row.get("segment_id"), {})
        rec = _rec(
            "high_visual_complexity",
            "low",
            0.58,
            [segment],
            [f"Segment {row.get('segment_id')} visual energy {row.get('visual_energy')}; mean complexity {row.get('mean_complexity')}; abruptness {row.get('abruptness')}."],
            "High visual complexity during dense explanation can compete with abstract claims or detailed reasoning.",
            f"Use stillness or lower complexity during abstract claim in segment {row.get('segment_id')} if human review confirms overload.",
            "Improves review focus without automatically changing media.",
            {"composition_summary": row},
        )
        rec["visual_evidence"] = row
        rec["review_action"] = "Review complexity against transcript density and rhetorical mode."
        rec["limitations"] = ["Complexity is a pixel/edge/color proxy, not an object or intent interpretation."]
        recommendations.append(rec)

    outputs["recommendations"] = sorted(
        recommendations,
        key=lambda item: (-{"high": 3, "medium": 2, "low": 1}.get(item.get("severity"), 0), -float(item.get("confidence") or 0.0), item.get("issue_type", "")),
    )
    outputs["visual_grounding"] = {
        "visual_boundary_alignment_summary": alignment.get("summary", {}),
        "visual_continuity_score": continuity.get("visual_continuity_score"),
        "composition_summary": composition.get("summary", {}),
        "limitations": [
            "Visual recommendations are proposal-only review notes.",
            "They do not mutate videos, timelines, renders, or boundaries.",
        ],
    }
    outputs["markdown"] = _markdown_with_consensus(outputs)
    return outputs


def _markdown_with_consensus(outputs: dict) -> str:
    lines = [
        "# Recommendations",
        "",
        "These recommendations are evidence-backed editorial proposals generated from local deterministic artifacts.",
        "",
        "Consensus outputs are deterministic evidence-fusion heuristics intended to improve explainability and editorial review. They are not semantic truth guarantees or autonomous editorial decisions.",
        "",
        "## Evidence-Ranked Recommendations",
        "",
    ]
    rows = outputs.get("recommendations") or []
    if not rows:
        lines.append("- No high-priority heuristic recommendations were produced.")
    for item in rows[:14]:
        backing = item.get("consensus_backing") or {}
        downgrade = ", ".join(backing.get("confidence_downgrade_reason") or []) or "none"
        warnings = ", ".join(backing.get("conflicting_evidence_warnings") or []) or "none"
        lines.append(
            f"- `{item.get('issue_type')}` ({item.get('severity')}, confidence {item.get('confidence')}): "
            f"{item.get('suggested_edit')} Consensus `{backing.get('consensus_score')}`, "
            f"agreement `{backing.get('modality_agreement_strength')}`, continuity `{backing.get('continuity_impact')}`, "
            f"false-positive risk `{backing.get('false_positive_risk')}`, conflicts `{warnings}`, downgrade `{downgrade}`."
        )
    lines.extend(["", "## Human Review Checklist", ""])
    lines.append("- Verify transcript accuracy before using recommendations for editing decisions.")
    lines.append("- Review conflicting modality evidence before acting on a segment-specific proposal.")
    lines.append("- Treat all recommendations as proposal-only; no source video, render, or timeline mutation is performed.")
    return "\n".join(lines) + "\n"
