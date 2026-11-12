"""Deterministic timeline overlay generation from existing artifacts."""

from __future__ import annotations

from intelligence_common import base_artifact, num
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


OVERLAY_TYPES = [
    "speech_pacing_overlay", "acoustic_energy_overlay", "silence_overlay", "rhetorical_pressure_overlay",
    "topic_continuity_overlay", "visual_reset_overlay", "boundary_diagnostic_overlay", "recommendation_overlay",
    "blocker_overlay", "archetype_overlay", "governance_overlay",
]


def _severity(score: float) -> str:
    return "high" if score >= 0.75 else "medium" if score >= 0.45 else "low"


def build_timeline_overlay_registry(analyses: list[dict], temporal_index: dict) -> dict:
    overlays = []
    for entry in temporal_index.get("temporal_evidence_entries") or []:
        scores = {row["signal"]: num(row.get("score")) for row in entry.get("strongest_signals") or []}
        recs = entry.get("recommendations") or []
        blockers = entry.get("blockers") or []
        candidates = [
            ("speech_pacing_overlay", scores.get("speech_pacing", 0.0), {"speech_pacing": scores.get("speech_pacing", 0.0)}),
            ("rhetorical_pressure_overlay", scores.get("rhetorical_pressure", 0.0), {"pressure_score": scores.get("rhetorical_pressure", 0.0)}),
            ("topic_continuity_overlay", scores.get("topic_drift", 0.0), {"topic_drift": scores.get("topic_drift", 0.0)}),
            ("visual_reset_overlay", scores.get("visual_reset", 0.0), {"low_visual_reset_signal": scores.get("visual_reset", 0.0)}),
        ]
        if recs:
            candidates.append(("recommendation_overlay", min(1.0, len(recs) / 3.0), {"recommendation_count": len(recs)}))
        if blockers:
            candidates.append(("blocker_overlay", 1.0, {"blocker_count": len(blockers)}))
        for overlay_type, score, values in candidates:
            if score <= 0:
                continue
            overlays.append(
                {
                    "overlay_id": deterministic_id("TOVR", entry.get("video_id"), entry.get("segment_id"), overlay_type),
                    "video_id": entry.get("video_id"),
                    "source_video": entry.get("source_video"),
                    "segment_id": entry.get("segment_id"),
                    "start_time": entry.get("timestamp_start"),
                    "end_time": entry.get("timestamp_end"),
                    "overlay_type": overlay_type,
                    "severity": _severity(score),
                    "confidence": round(max(0.35, min(0.9, score)), 3),
                    "metric_values": values,
                    "interpretation": "Candidate timeline review signal; inspect source segment before making editorial changes.",
                    "evidence_refs": entry.get("evidence_refs") or [],
                    "related_recommendations": recs,
                    "related_detail_pages": [f"visualizations/timeline/segment_context_{entry.get('video_id')}_{entry.get('segment_id')}.html"],
                    "suggested_review_action": entry.get("suggested_review_action"),
                    "non_claim_limitation": LIMITATION,
                }
            )
    output = base_artifact(method="deterministic_timeline_overlay_system_v1")
    output.update(
        {
            "timeline_overlay_registry_id": deterministic_id("TOVREG", [(row["overlay_id"], row["severity"]) for row in overlays]),
            "overlay_types": OVERLAY_TYPES,
            "overlays": overlays,
            "summary": {"overlay_count": len(overlays), "overlay_type_count": len(OVERLAY_TYPES)},
            "limitations": [LIMITATION],
        }
    )
    return output


def build_timeline_recommendation_pins(recommendation_traceability: dict) -> dict:
    pins = []
    for row in recommendation_traceability.get("traceability_entries") or []:
        for segment in row.get("affected_segments") or []:
            pins.append(
                {
                    "pin_id": deterministic_id("TRPIN", row.get("recommendation_id"), segment.get("segment_id")),
                    "recommendation_id": row.get("recommendation_id"),
                    "video_id": segment.get("video_id"),
                    "source_video": segment.get("source_video"),
                    "segment_id": segment.get("segment_id"),
                    "start_time": segment.get("start_time"),
                    "end_time": segment.get("end_time"),
                    "severity": row.get("severity"),
                    "priority_score": row.get("priority_score"),
                    "title": row.get("title"),
                    "detail_page": "visualizations/recommendation_traceability.html",
                    "evidence_refs": row.get("evidence_refs") or [],
                }
            )
    output = base_artifact(method="deterministic_timeline_recommendation_pins_v1")
    output.update({"timeline_recommendation_pins_id": deterministic_id("TRPREG", [pin["pin_id"] for pin in pins]), "recommendation_pins": pins, "summary": {"recommendation_pin_count": len(pins)}, "limitations": [LIMITATION]})
    return output


def build_timeline_metric_spikes(temporal_index: dict) -> dict:
    spikes = []
    for entry in temporal_index.get("temporal_evidence_entries") or []:
        for signal in entry.get("strongest_signals") or []:
            if num(signal.get("score")) < 0.45:
                continue
            spikes.append(
                {
                    "metric_spike_id": deterministic_id("TMSPK", entry.get("video_id"), entry.get("segment_id"), signal.get("signal")),
                    "video_id": entry.get("video_id"),
                    "source_video": entry.get("source_video"),
                    "segment_id": entry.get("segment_id"),
                    "start_time": entry.get("timestamp_start"),
                    "end_time": entry.get("timestamp_end"),
                    "metric_id": signal.get("signal"),
                    "spike_score": signal.get("score"),
                    "severity": _severity(num(signal.get("score"))),
                    "interpretation": "Directional metric spike for human review.",
                    "evidence_refs": entry.get("evidence_refs") or [],
                }
            )
    output = base_artifact(method="deterministic_timeline_metric_spikes_v1")
    output.update({"timeline_metric_spikes_id": deterministic_id("TMSREG", [row["metric_spike_id"] for row in spikes]), "metric_spikes": spikes, "summary": {"metric_spike_count": len(spikes)}, "limitations": [LIMITATION]})
    return output

