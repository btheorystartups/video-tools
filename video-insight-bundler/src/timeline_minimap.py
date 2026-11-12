"""Compact deterministic timeline minimaps for reviewer navigation."""

from __future__ import annotations

from collections import Counter

from intelligence_common import base_artifact, num
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


def _band(entry: dict) -> dict:
    severity = (entry.get("highest_severity_signal") or {}).get("severity") or "low"
    score = num((entry.get("highest_severity_signal") or {}).get("score"))
    return {
        "segment_id": entry.get("segment_id"),
        "start_time": entry.get("timestamp_start"),
        "end_time": entry.get("timestamp_end"),
        "severity": severity,
        "score": round(score, 3),
        "timeline_anchor": f"segment-{entry.get('segment_id')}",
    }


def build_timeline_minimap_registry(temporal_index: dict, pins: dict, spikes: dict) -> dict:
    by_video: dict[str, list[dict]] = {}
    for entry in temporal_index.get("temporal_evidence_entries") or []:
        by_video.setdefault(entry.get("video_id"), []).append(entry)
    pin_counts = Counter(pin.get("video_id") for pin in pins.get("recommendation_pins") or [])
    spike_counts = Counter(row.get("video_id") for row in spikes.get("metric_spikes") or [])
    minimaps = []
    for video_id, entries in sorted(by_video.items()):
        ordered = sorted(entries, key=lambda row: (num(row.get("timestamp_start")), row.get("segment_id") or ""))
        duration = max([num(row.get("timestamp_end")) for row in ordered] or [0.0])
        high_regions = [row for row in ordered if (row.get("highest_severity_signal") or {}).get("severity") == "high"]
        minimaps.append(
            {
                "minimap_id": deterministic_id("TMM", video_id, [(row.get("segment_id"), row.get("timestamp_start")) for row in ordered]),
                "video_id": video_id,
                "corpus_id": None,
                "source_video": ordered[0].get("source_video") if ordered else None,
                "duration": duration,
                "segment_count": len(ordered),
                "severity_bands": [_band(row) for row in ordered],
                "recommendation_density": round(pin_counts.get(video_id, 0) / max(1, len(ordered)), 3),
                "blocker_density": round(sum(len(row.get("blockers") or []) for row in ordered) / max(1, len(ordered)), 3),
                "metric_spike_density": round(spike_counts.get(video_id, 0) / max(1, len(ordered)), 3),
                "high_priority_regions": [
                    {
                        "segment_id": row.get("segment_id"),
                        "start_time": row.get("timestamp_start"),
                        "end_time": row.get("timestamp_end"),
                        "severity": (row.get("highest_severity_signal") or {}).get("severity"),
                        "review_value": row.get("suggested_review_action"),
                    }
                    for row in high_regions
                ],
                "links_to_timeline_regions": [
                    {
                        "segment_id": row.get("segment_id"),
                        "target_path": f"visualizations/timeline/enhanced_video_timeline_{video_id}.html",
                        "target_anchor": f"segment-{row.get('segment_id')}",
                    }
                    for row in ordered
                ],
                "evidence_refs": sorted({ref for row in ordered for ref in (row.get("evidence_refs") or [])}),
                "non_claim_limitation": LIMITATION,
            }
        )
    corpus_bands = []
    for minimap in minimaps:
        high_count = sum(1 for band in minimap.get("severity_bands") or [] if band.get("severity") == "high")
        corpus_bands.append({"video_id": minimap.get("video_id"), "high_region_count": high_count, "segment_count": minimap.get("segment_count")})
    output = base_artifact(method="deterministic_timeline_minimap_v1")
    output.update(
        {
            "timeline_minimap_registry_id": deterministic_id("TMMREG", [row["minimap_id"] for row in minimaps]),
            "minimaps": minimaps,
            "corpus_minimap": {
                "minimap_id": deterministic_id("TMMCORPUS", corpus_bands),
                "corpus_id": "local_corpus",
                "severity_bands": corpus_bands,
                "target_path": "visualizations/timeline/enhanced_corpus_timeline_overview.html",
            },
            "summary": {"minimap_count": len(minimaps), "segment_count": sum(row.get("segment_count", 0) for row in minimaps)},
            "limitations": [LIMITATION],
        }
    )
    return output
