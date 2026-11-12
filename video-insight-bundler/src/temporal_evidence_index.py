"""Unified temporal evidence index for static timeline review."""

from __future__ import annotations

from collections import Counter

from intelligence_common import base_artifact, num
from stability import STATUS_COMPLETE, deterministic_id

LIMITATION = "This page provides deterministic editorial-review guidance. It does not infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required."


def _video_id(source_video: str | None) -> str:
    return deterministic_id("VID", source_video or "unknown", length=10)


def _severity(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _analysis_segments(analysis: dict) -> list[dict]:
    return sorted((analysis.get("scene_segments") or {}).get("segments") or [], key=lambda row: (num(row.get("start_sec")), row.get("segment_id") or ""))


def _recommendations_for_segment(analysis: dict, segment_id: str | None) -> list[dict]:
    return [row for row in (analysis.get("recommendations") or {}).get("recommendations") or [] if segment_id in (row.get("affected_segment_ids") or [])]


def _pressure_by_segment(analysis: dict) -> dict:
    rows = (((analysis.get("editorial_pressure") or {}).get("summary") or {}).get("chronic_pressure_regions") or [])
    return {row.get("segment_id"): num(row.get("cumulative_pressure_score") or row.get("pressure_score")) for row in rows}


def _argument_flags(analysis: dict) -> dict:
    argument = analysis.get("argument_graph") or {}
    unresolved = len(argument.get("unresolved_chains") or [])
    contradictions = len(argument.get("contradiction_clusters") or [])
    return {"unresolved_claims": unresolved, "contradiction_clusters": contradictions}


def build_temporal_evidence_index(analyses: list[dict]) -> dict:
    entries = []
    for analysis in analyses:
        manifest = analysis.get("manifest") or {}
        source_video = manifest.get("source_video")
        vid = _video_id(source_video)
        analysis_dir = analysis.get("analysis_dir")
        pressure = _pressure_by_segment(analysis)
        flags = _argument_flags(analysis)
        visual_score = num(((analysis.get("visual_continuity") or analysis.get("visual_structure") or {}).get("visual_continuity_score")), 0.5)
        for segment in _analysis_segments(analysis):
            segment_id = segment.get("segment_id")
            recs = _recommendations_for_segment(analysis, segment_id)
            wpm = num(segment.get("speech_rate_wpm") or segment.get("words_per_minute"))
            pressure_score = pressure.get(segment_id, 0.0)
            drift = 1.0 - num(segment.get("segment_coherence_score"), 0.65)
            signal_scores = {
                "speech_pacing": min(1.0, wpm / 220.0) if wpm else 0.0,
                "rhetorical_pressure": pressure_score,
                "topic_drift": drift,
                "visual_reset": max(0.0, 1.0 - visual_score),
                "recommendations": min(1.0, len(recs) / 3.0),
                "blockers": 1.0 if any((rec.get("severity") == "high") for rec in recs) else 0.0,
            }
            strongest = sorted(signal_scores.items(), key=lambda item: (-item[1], item[0]))[:4]
            highest = strongest[0] if strongest else ("review", 0.0)
            entries.append(
                {
                    "temporal_evidence_id": deterministic_id("TEVIDX", source_video, segment_id, segment.get("start_sec"), segment.get("end_sec")),
                    "video_id": vid,
                    "source_video": source_video,
                    "analysis_dir": analysis_dir,
                    "segment_id": segment_id,
                    "timestamp_start": segment.get("start_sec"),
                    "timestamp_end": segment.get("end_sec"),
                    "evidence_types_present": [name for name, score in signal_scores.items() if score > 0],
                    "strongest_signals": [{"signal": name, "score": round(score, 3)} for name, score in strongest],
                    "highest_severity_signal": {"signal": highest[0], "severity": _severity(highest[1]), "score": round(highest[1], 3)},
                    "recommendations": [rec.get("issue_type") for rec in recs],
                    "blockers": [rec.get("issue_type") for rec in recs if rec.get("severity") == "high"],
                    "archetypes": [],
                    "relevant_graphs": ["graphs/editorial_pressure.png", "graphs/topic_continuity.png", "graphs/visual_continuity.png"],
                    "relevant_reports": ["reports/temporal_evidence_index_report.md"],
                    "suggested_review_action": "Open the segment context and review linked recommendation evidence." if recs or highest[1] >= 0.45 else "Scan as context for neighboring timeline regions.",
                    "evidence_refs": [f"{analysis_dir}/scene_segments.json#{segment_id}", f"{analysis_dir}/recommendations.json"],
                    "non_claim_limitation": LIMITATION,
                    "argument_flags": flags,
                }
            )
    counts = Counter(entry["highest_severity_signal"]["severity"] for entry in entries)
    output = base_artifact(method="deterministic_temporal_evidence_index_v1")
    output.update(
        {
            "temporal_evidence_index_id": deterministic_id("TEIREG", [(row["video_id"], row["segment_id"], row["highest_severity_signal"]["severity"]) for row in entries]),
            "temporal_evidence_entries": entries,
            "summary": {"temporal_evidence_entry_count": len(entries), "severity_counts": dict(counts)},
            "limitations": [LIMITATION, "Temporal evidence entries are local editorial heuristics and do not mutate media or timelines."],
        }
    )
    return output

