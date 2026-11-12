"""Deterministic narrative memory windows and resurfacing analysis."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean

from report_generator import STOPWORDS, keyword_counts, words
from stability import STATUS_COMPLETE, STATUS_LIMITED, deterministic_id


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def _tokens(text: str) -> set[str]:
    return {token for token in words(text) if len(token) > 2 and token not in STOPWORDS}


def _window(segments: list[dict], center: int, radius: int) -> dict:
    start = max(0, center - radius)
    end = min(len(segments), center + 1)
    rows = segments[start:end]
    text = " ".join(row.get("text", "") for row in rows)
    return {
        "window_id": deterministic_id("NMW", start, end, radius),
        "segment_ids": [row.get("segment_id") for row in rows],
        "top_terms": keyword_counts(text, 12),
    }


def analyze_narrative_memory(
    scene_segments: dict,
    discourse_state: dict | None = None,
    argument_graph: dict | None = None,
    topic_continuity: dict | None = None,
) -> dict:
    segments = scene_segments.get("segments") or []
    if not segments:
        return {
            "analysis_status": STATUS_LIMITED,
            "method": "deterministic_narrative_memory_v1",
            "memory_windows": {"short": [], "medium": [], "long": []},
            "persistent_themes": [],
            "callback_references": [],
            "delayed_resolutions": [],
            "resurfacing_concepts": [],
            "thematic_persistence_score": 0.0,
            "narrative_drift_score": 0.0,
            "narrative_recovery_score": 0.0,
            "limitations": ["No segments were available for narrative memory analysis."],
        }

    term_locations: dict[str, list[int]] = defaultdict(list)
    for index, segment in enumerate(segments):
        for token in _tokens(segment.get("text", "")):
            term_locations[token].append(index)

    short_windows = [_window(segments, index, 1) for index in range(len(segments))]
    medium_windows = [_window(segments, index, 4) for index in range(len(segments))]
    long_terms = [
        {"term": item["term"], "count": item["count"]}
        for item in keyword_counts(" ".join(segment.get("text", "") for segment in segments), 60)
    ]

    persistent_themes = []
    resurfacing = []
    callbacks = []
    for term, indexes in sorted(term_locations.items(), key=lambda item: (-len(set(item[1])), item[0])):
        unique_indexes = sorted(set(indexes))
        if len(unique_indexes) > 1:
            segment_ids = [segments[index].get("segment_id") for index in unique_indexes]
            persistent_themes.append(
                {
                    "theme_id": deterministic_id("NMT", term, ",".join(segment_ids)),
                    "term": term,
                    "segment_ids": segment_ids,
                    "span_segments": unique_indexes[-1] - unique_indexes[0] + 1,
                    "occurrence_count": len(unique_indexes),
                }
            )
        gaps = [right - left for left, right in zip(unique_indexes, unique_indexes[1:])]
        for left, right, gap in zip(unique_indexes, unique_indexes[1:], gaps):
            if gap >= 2:
                row = {
                    "reference_id": deterministic_id("NMR", term, segments[left].get("segment_id"), segments[right].get("segment_id")),
                    "term": term,
                    "from_segment_id": segments[left].get("segment_id"),
                    "to_segment_id": segments[right].get("segment_id"),
                    "latency_segments": gap,
                }
                resurfacing.append(row)
                callbacks.append({**row, "callback_type": "long_memory_return" if gap >= 5 else "medium_memory_return"})

    unresolved_ids = {chain.get("root_node_id") for chain in (argument_graph or {}).get("unresolved_chains", [])}
    delayed_resolutions = []
    for chain in (argument_graph or {}).get("recovered_chains", []):
        segments_in_chain = chain.get("segment_ids") or []
        if len(segments_in_chain) >= 2:
            delayed_resolutions.append(
                {
                    "resolution_id": deterministic_id("NMD", chain.get("chain_id"), ",".join(segments_in_chain)),
                    "chain_id": chain.get("chain_id"),
                    "setup_segment_id": segments_in_chain[0],
                    "resolution_segment_id": segments_in_chain[-1],
                    "latency_segments": max(0, len(segments_in_chain) - 1),
                    "resolution_strength": chain.get("chain_strength"),
                }
            )

    bridge_scores = [float(row.get("continuity_score") or 0.0) for row in (topic_continuity or {}).get("topic_bridge_terms", [])]
    drift = _clamp(1.0 - (mean(bridge_scores) if bridge_scores else 0.5))
    persistence = _clamp(min(len(persistent_themes), max(len(segments), 1)) / max(len(segments), 1))
    recovery = _clamp((len(delayed_resolutions) + len(callbacks) * 0.35) / max(len(resurfacing) + len(unresolved_ids), 1))
    return {
        "analysis_status": STATUS_COMPLETE if any(segment.get("text") for segment in segments) else STATUS_LIMITED,
        "method": "deterministic_narrative_memory_v1",
        "memory_windows": {
            "short": short_windows,
            "medium": medium_windows,
            "long": [{"window_id": deterministic_id("NML", len(segments)), "segment_ids": [segment.get("segment_id") for segment in segments], "top_terms": long_terms[:24]}],
        },
        "persistent_themes": persistent_themes[:60],
        "callback_references": callbacks[:80],
        "delayed_resolutions": delayed_resolutions[:60],
        "unresolved_callbacks": [
            {
                "callback_id": row.get("item_id"),
                "segment_id": row.get("segment_id"),
                "concepts": row.get("concepts", []),
            }
            for row in (discourse_state or {}).get("segment_discourse_states", [])
            if row.get("state_events", {}).get("has_callback") and row.get("discourse_pressure_score", 0) > 0.45
        ][:40],
        "resurfacing_concepts": resurfacing[:80],
        "thematic_persistence_score": persistence,
        "narrative_drift_score": drift,
        "narrative_recovery_score": recovery,
        "limitations": [
            "Narrative memory uses deterministic token recurrence and chain timing.",
            "It does not infer author intent or semantic equivalence.",
        ],
    }
