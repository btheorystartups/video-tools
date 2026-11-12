"""Temporal severity and evidence density heatmaps."""

from __future__ import annotations

from collections import Counter

from intelligence_common import base_artifact, num
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


def build_temporal_heatmap_registry(temporal_index: dict, pins: dict, spikes: dict) -> dict:
    pin_counts = Counter((row.get("video_id"), row.get("segment_id")) for row in pins.get("recommendation_pins") or [])
    spike_counts = Counter((row.get("video_id"), row.get("segment_id")) for row in spikes.get("metric_spikes") or [])
    by_video: dict[str, list[dict]] = {}
    for entry in temporal_index.get("temporal_evidence_entries") or []:
        by_video.setdefault(entry.get("video_id"), []).append(entry)
    heatmaps = []
    for video_id, entries in sorted(by_video.items()):
        cells = []
        for entry in sorted(entries, key=lambda row: (num(row.get("timestamp_start")), row.get("segment_id") or "")):
            signals = {row.get("signal"): num(row.get("score")) for row in entry.get("strongest_signals") or []}
            cells.append(
                {
                    "cell_id": deterministic_id("THCELL", video_id, entry.get("segment_id")),
                    "segment_id": entry.get("segment_id"),
                    "time_region": [entry.get("timestamp_start"), entry.get("timestamp_end")],
                    "severity": (entry.get("highest_severity_signal") or {}).get("severity"),
                    "evidence_density": len(entry.get("evidence_refs") or []),
                    "recommendation_density": pin_counts.get((video_id, entry.get("segment_id")), 0),
                    "blocker_density": len(entry.get("blockers") or []),
                    "acoustic_intensity": signals.get("acoustic_energy", 0.0),
                    "pacing_pressure": signals.get("speech_pacing", 0.0),
                    "rhetorical_pressure": signals.get("rhetorical_pressure", 0.0),
                    "visual_reset_scarcity": signals.get("visual_reset", 0.0),
                    "topic_drift": signals.get("topic_drift", 0.0),
                    "metric_spike_density": spike_counts.get((video_id, entry.get("segment_id")), 0),
                }
            )
        heatmaps.append({"heatmap_id": deterministic_id("THMAP", video_id, [row["cell_id"] for row in cells]), "video_id": video_id, "source_video": entries[0].get("source_video") if entries else None, "cells": cells, "html_page": f"visualizations/timeline/timeline_heatmap_{video_id}.html", "non_claim_limitation": LIMITATION})
    output = base_artifact(method="deterministic_temporal_heatmap_v1")
    output.update({"temporal_heatmap_registry_id": deterministic_id("THMAPREG", [row["heatmap_id"] for row in heatmaps]), "heatmaps": heatmaps, "summary": {"heatmap_count": len(heatmaps), "cell_count": sum(len(row.get("cells") or []) for row in heatmaps)}, "limitations": [LIMITATION]})
    return output
