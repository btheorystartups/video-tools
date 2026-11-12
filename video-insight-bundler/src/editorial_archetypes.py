"""Deterministic editorial archetype detection for corpus review."""

from __future__ import annotations

from intelligence_common import base_artifact, clamp, deterministic_id


def _match_archetypes(analysis: dict) -> list[dict]:
    readiness = analysis.get("release_readiness") or {}
    visual = analysis.get("visual_structure") or {}
    temporal = analysis.get("temporal_rhythm") or {}
    pressure = analysis.get("editorial_pressure") or {}
    callback = analysis.get("callback_resolution") or {}
    argument = analysis.get("argument_graph") or {}
    discourse = analysis.get("discourse_state") or {}
    peak_pressure = ((pressure.get("summary") or {}).get("peak_cumulative_pressure_score") or 0.0)
    intensity = ((temporal.get("summary") or {}).get("mean_intensity_wave_score") or 0.0)
    visual_cont = visual.get("visual_continuity_score") or 0.0
    readiness_score = readiness.get("release_readiness_score") or 0.0
    rows = []

    def add(name: str, score: float, reason: str) -> None:
        if score >= 0.45:
            rows.append(
                {
                    "archetype_match_id": deterministic_id("ARCH", analysis.get("analysis_dir"), name, round(score, 3)),
                    "archetype": name,
                    "match_score": clamp(score),
                    "reason": reason,
                    "analysis_dir": analysis.get("analysis_dir"),
                    "source_video": (analysis.get("manifest") or {}).get("source_video"),
                }
            )

    add("stable_reflective_monologue", (readiness_score * 0.45) + ((1.0 - intensity) * 0.35) + (visual_cont * 0.2), "Moderate readiness with low pacing volatility and sustained visual continuity.")
    add("high_pressure_abstract_argument", peak_pressure * 0.62 + (1.0 - readiness_score) * 0.38, "High cumulative pressure and readiness drag.")
    add("visually_static_philosophical_riff", visual_cont * 0.55 + ((discourse.get("discourse_pressure_score") or 0.0) * 0.45), "Visual continuity is high while discourse pressure remains visible.")
    add("compressed_rhetorical_escalation", intensity * 0.6 + min((temporal.get("summary") or {}).get("density_spike_count") or 0, 5) / 5.0 * 0.4, "Dense pacing wave with repeated density spikes.")
    add("unresolved_callback_heavy_talk", (1.0 - (callback.get("payoff_quality_score") or 0.5)) * 0.55 + min(len(callback.get("unresolved_setups") or []), 4) / 4.0 * 0.45, "Callback payoff quality or unresolved setup count needs review.")
    add("low_visual_reset_discourse_flow", visual_cont * 0.5 + ((discourse.get("discourse_pressure_score") or 0.0) * 0.5), "Sustained visual continuity with active discourse pressure.")
    add("high_contradiction_pressure_sequence", min(len(argument.get("contradiction_clusters") or []), 4) / 4.0 * 0.5 + peak_pressure * 0.5, "Contradiction clusters and cumulative pressure co-occur.")
    return sorted(rows, key=lambda row: (-row["match_score"], row["archetype"]))


def build_editorial_archetypes(analyses: list[dict]) -> dict:
    matches = []
    for analysis in analyses:
        matches.extend(_match_archetypes(analysis))
    counts = {}
    for row in matches:
        counts[row["archetype"]] = counts.get(row["archetype"], 0) + 1
    output = base_artifact(method="deterministic_editorial_archetype_matching_v1")
    output.update(
        {
            "editorial_archetype_id": deterministic_id("ARCHSET", sorted(counts.items()), len(analyses)),
            "archetype_matches": matches,
            "archetype_counts": dict(sorted(counts.items())),
            "dominant_archetypes": sorted(
                [{"archetype": key, "count": value} for key, value in counts.items()],
                key=lambda row: (-row["count"], row["archetype"]),
            ),
            "summary": {
                "analysis_count": len(analyses),
                "archetype_match_count": len(matches),
                "distinct_archetype_count": len(counts),
            },
        }
    )
    return output
