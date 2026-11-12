"""Segment context panel artifacts and page models."""

from __future__ import annotations

from intelligence_common import base_artifact
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


def build_segment_context_panels(temporal_index: dict, traceability: dict, max_panels: int = 80) -> dict:
    rec_by_segment = {}
    for rec in traceability.get("traceability_entries") or []:
        for seg in rec.get("affected_segments") or []:
            rec_by_segment.setdefault((seg.get("video_id"), seg.get("segment_id")), []).append(rec.get("recommendation_id"))
    entries = sorted(temporal_index.get("temporal_evidence_entries") or [], key=lambda row: ({"high": 0, "medium": 1, "low": 2}.get((row.get("highest_severity_signal") or {}).get("severity"), 3), row.get("source_video") or "", row.get("timestamp_start") or 0))[:max_panels]
    panels = []
    for entry in entries:
        panel_id = deterministic_id("SCTX", entry.get("video_id"), entry.get("segment_id"))
        panels.append({"segment_context_panel_id": panel_id, "video_id": entry.get("video_id"), "source_video": entry.get("source_video"), "segment_id": entry.get("segment_id"), "start_time": entry.get("timestamp_start"), "end_time": entry.get("timestamp_end"), "page_path": f"visualizations/timeline/segment_context_{entry.get('video_id')}_{entry.get('segment_id')}.html", "pacing_metrics": [row for row in entry.get("strongest_signals") or [] if row.get("signal") == "speech_pacing"], "acoustic_metrics": [], "rhetorical_metrics": [row for row in entry.get("strongest_signals") or [] if row.get("signal") == "rhetorical_pressure"], "visual_metrics": [row for row in entry.get("strongest_signals") or [] if row.get("signal") == "visual_reset"], "topic_continuity_metrics": [row for row in entry.get("strongest_signals") or [] if row.get("signal") == "topic_drift"], "recommendations": rec_by_segment.get((entry.get("video_id"), entry.get("segment_id")), []), "blockers": entry.get("blockers") or [], "archetypes": entry.get("archetypes") or [], "evidence_refs": entry.get("evidence_refs") or [], "optimization_guidance": "Use the lowest-risk linked recommendation path; do not mutate media from this page.", "what_to_preserve": "Preserve intentional pacing, silence, abstraction, and tension when human review supports them.", "what_to_review": entry.get("suggested_review_action"), "what_not_to_infer": "Identity, face recognition, actual emotion, diagnosis, personality, or viewer behavior.", "non_claim_limitation": LIMITATION})
    output = base_artifact(method="deterministic_segment_context_panels_v1")
    output.update({"segment_context_panels_id": deterministic_id("SCTXREG", [row["segment_context_panel_id"] for row in panels]), "segment_context_panels": panels, "summary": {"segment_context_panel_count": len(panels)}, "limitations": [LIMITATION]})
    return output

