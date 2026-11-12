"""Segment-level deterministic drilldowns for expert review workflows."""

from __future__ import annotations

from pathlib import Path

from intelligence_common import base_artifact, num
from stability import deterministic_id


def _severity(segment: dict, recommendations: list[dict], pressure: float) -> str:
    wpm = num(segment.get("speech_rate_wpm") or segment.get("words_per_minute"))
    if pressure >= 0.75 or wpm >= 195 or len(recommendations) >= 2:
        return "high"
    if pressure >= 0.5 or wpm >= 170 or recommendations:
        return "medium"
    return "low"


def build_segment_drilldown_index(analyses: list[dict]) -> dict:
    rows = []
    pages = []
    for analysis in analyses:
        manifest = analysis.get("manifest") or {}
        source_video = manifest.get("source_video")
        analysis_dir = analysis.get("analysis_dir")
        recs = (analysis.get("recommendations") or {}).get("recommendations") or []
        pressure_rows = (((analysis.get("editorial_pressure") or {}).get("summary") or {}).get("chronic_pressure_regions") or [])
        pressure_by_segment = {row.get("segment_id"): num(row.get("cumulative_pressure_score") or row.get("pressure_score")) for row in pressure_rows}
        segment_rows = []
        for segment in (analysis.get("scene_segments") or {}).get("segments") or []:
            segment_id = segment.get("segment_id")
            related = [rec for rec in recs if segment_id in (rec.get("affected_segment_ids") or [])]
            pressure = pressure_by_segment.get(segment_id, 0.0)
            severity = _severity(segment, related, pressure)
            row = {
                "segment_drilldown_id": deterministic_id("SDRILL", source_video, segment_id, severity),
                "source_video": source_video,
                "analysis_dir": analysis_dir,
                "segment_id": segment_id,
                "start_sec": segment.get("start_sec"),
                "end_sec": segment.get("end_sec"),
                "severity": severity,
                "related_metrics": {
                    "speech_rate_wpm": segment.get("speech_rate_wpm") or segment.get("words_per_minute"),
                    "segment_coherence_score": segment.get("segment_coherence_score"),
                    "pressure_score": round(pressure, 3),
                    "recommendation_count": len(related),
                },
                "related_recommendations": [rec.get("issue_type") for rec in related if rec.get("issue_type")],
                "suggested_review_action": "Review this segment before changing pacing, structure, or visuals." if severity != "low" else "Scan only if this segment is part of a larger pattern.",
                "evidence_refs": [f"{analysis_dir}/scene_segments.json#{segment_id}"] + [f"{analysis_dir}/recommendations.json" for _ in related[:1]],
            }
            rows.append(row)
            segment_rows.append(row)
        pages.append(
            {
                "page_id": deterministic_id("SDPAGE", source_video, len(segment_rows)),
                "source_video": source_video,
                "detail_page": f"visualizations/detail/segment_drilldown_{deterministic_id('VID', source_video, length=10)}.html",
                "segment_count": len(segment_rows),
                "high_severity_count": sum(1 for row in segment_rows if row["severity"] == "high"),
                "evidence_refs": ["scene_segments.json", "recommendations.json", "sequence/editorial_pressure.json"],
            }
        )
    output = base_artifact(method="deterministic_segment_drilldown_v1")
    output.update(
        {
            "segment_drilldown_index_id": deterministic_id("SDINDEX", [(row["source_video"], row["segment_id"], row["severity"]) for row in rows]),
            "segment_drilldowns": rows,
            "detail_pages": pages,
            "summary": {"segment_drilldown_count": len(rows), "detail_page_count": len(pages), "high_severity_count": sum(1 for row in rows if row["severity"] == "high")},
        }
    )
    return output
