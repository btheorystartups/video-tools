"""Editorial pressure accumulation model."""

from __future__ import annotations

from intelligence_common import avg, base_artifact, clamp, deterministic_id, num, recommendation_rows, sorted_segments


def _ids(rows: list[dict], key: str) -> set[str]:
    return {row.get(key) for row in rows if row.get(key)}


def build_editorial_pressure(bundle, temporal_rhythm: dict | None = None, narrative_phase_model: dict | None = None) -> dict:
    segments = sorted_segments(bundle.scene_segments)
    rhythm_by_id = {row.get("segment_id"): row for row in (temporal_rhythm or {}).get("rhythm_segments", [])}
    phase_by_id = {row.get("segment_id"): row for row in (narrative_phase_model or {}).get("phase_segments", [])}
    discourse = getattr(bundle, "discourse_state", None) or {}
    argument = getattr(bundle, "argument_graph", None) or {}
    callback = getattr(bundle, "callback_resolution", None) or {}
    ambiguity = getattr(bundle, "editorial_ambiguity", None) or {}
    boundary = getattr(bundle, "boundary_diagnostics", None) or {}
    recs = recommendation_rows(bundle)
    unresolved_questions = _ids((getattr(bundle, "rhetorical_coherence", None) or {}).get("unresolved_questions") or [], "segment_id")
    unresolved_chains = {sid for chain in argument.get("unresolved_chains", []) for sid in chain.get("segment_ids", [])}
    unresolved_callbacks = _ids(callback.get("unresolved_setups") or [], "setup_segment_id")
    ambiguous_segments = {row.get("from_segment_id") for row in ambiguity.get("ambiguity_regions", [])} | {row.get("to_segment_id") for row in ambiguity.get("ambiguity_regions", [])}
    rec_segments = {sid for rec in recs for sid in rec.get("affected_segment_ids", [])}
    review_boundaries = {row.get("to_segment_id") for row in boundary.get("boundaries", []) if row.get("likely_review_boundary")}
    rows = []
    cumulative = 0.0
    for segment in segments:
        sid = segment.get("segment_id")
        rhythm = rhythm_by_id.get(sid, {})
        phase = phase_by_id.get(sid, {})
        unresolved_claims = 1.0 if sid in unresolved_chains or sid in unresolved_questions else 0.0
        callback_debt = 1.0 if sid in unresolved_callbacks else 0.0
        contradiction = min(len(argument.get("contradiction_clusters") or []) / max(len(segments), 1), 1.0)
        rhetorical_debt = 1.0 if phase.get("phase") == "unresolved_exit" else 0.0
        pacing_overload = 1.0 if rhythm.get("wave_class") in {"density_spike", "pacing_acceleration"} and num(rhythm.get("density_score")) > 0.68 else 0.0
        ambiguity_pressure = 1.0 if sid in ambiguous_segments else 0.0
        transition_pressure = 1.0 if sid in review_boundaries else 0.0
        recommendation_pressure = 1.0 if sid in rec_segments else 0.0
        pressure_score = clamp(
            unresolved_claims * 0.17
            + callback_debt * 0.14
            + contradiction * 0.13
            + rhetorical_debt * 0.12
            + pacing_overload * 0.13
            + ambiguity_pressure * 0.11
            + transition_pressure * 0.1
            + recommendation_pressure * 0.1
        )
        cumulative = clamp(cumulative * 0.72 + pressure_score * 0.58)
        rows.append(
            {
                "pressure_id": deterministic_id("PRESS", sid, pressure_score, cumulative),
                "segment_id": sid,
                "start_sec": segment.get("start_sec"),
                "end_sec": segment.get("end_sec"),
                "pressure_score": pressure_score,
                "cumulative_pressure_score": cumulative,
                "pressure_class": "high" if pressure_score >= 0.62 else "medium" if pressure_score >= 0.34 else "low",
                "components": {
                    "unresolved_claims": unresolved_claims,
                    "unresolved_callbacks": callback_debt,
                    "contradiction_accumulation": round(contradiction, 3),
                    "rhetorical_debt": rhetorical_debt,
                    "pacing_overload": pacing_overload,
                    "ambiguity_accumulation": ambiguity_pressure,
                    "unsupported_transitions": transition_pressure,
                    "recommendation_pressure": recommendation_pressure,
                },
            }
        )
    output = base_artifact(method="deterministic_editorial_pressure_v1")
    output.update(
        {
            "pressure_segments": rows,
            "summary": {
                "segment_count": len(rows),
                "mean_pressure_score": avg([row["pressure_score"] for row in rows]),
                "peak_pressure_score": max([row["pressure_score"] for row in rows], default=0.0),
                "peak_cumulative_pressure_score": max([row["cumulative_pressure_score"] for row in rows], default=0.0),
                "high_pressure_segment_count": sum(1 for row in rows if row["pressure_class"] == "high"),
                "chronic_pressure_regions": [row for row in rows if row["cumulative_pressure_score"] >= 0.58],
                "discourse_pressure_score": discourse.get("discourse_pressure_score"),
            },
        }
    )
    return output
