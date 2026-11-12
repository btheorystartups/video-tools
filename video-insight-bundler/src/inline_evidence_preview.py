"""Inline evidence preview index for static workstation pages."""

from __future__ import annotations

from intelligence_common import base_artifact, num
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


def build_inline_evidence_preview_index(temporal_index: dict, traceability: dict) -> dict:
    previews = []
    seen = set()
    for entry in temporal_index.get("temporal_evidence_entries") or []:
        severity = (entry.get("highest_severity_signal") or {}).get("severity")
        signal = (entry.get("highest_severity_signal") or {}).get("signal")
        value = num((entry.get("highest_severity_signal") or {}).get("score"))
        for ref in entry.get("evidence_refs") or []:
            key = (entry.get("video_id"), entry.get("segment_id"), ref)
            if key in seen:
                continue
            seen.add(key)
            previews.append(
                {
                    "evidence_preview_id": deterministic_id("IEP", *key),
                    "evidence_title": f"{entry.get('segment_id')} {signal} evidence",
                    "artifact_path": ref.split("#")[0],
                    "artifact_type": "json",
                    "video_id": entry.get("video_id"),
                    "segment_id": entry.get("segment_id"),
                    "metric_summary": signal,
                    "relevant_value": round(value, 3),
                    "severity": severity,
                    "confidence": round(max(0.35, min(0.9, value)), 3),
                    "short_interpretation": "Directional evidence preview for human review.",
                    "open_full_artifact_link": ref.split("#")[0],
                    "open_related_detail_page_link": f"visualizations/timeline/segment_context_{entry.get('video_id')}_{entry.get('segment_id')}.html",
                    "non_claim_limitation": LIMITATION,
                }
            )
    output = base_artifact(method="deterministic_inline_evidence_preview_v1")
    output.update({"inline_evidence_preview_index_id": deterministic_id("IEPREG", [row["evidence_preview_id"] for row in previews]), "evidence_previews": previews, "summary": {"evidence_preview_count": len(previews)}, "limitations": [LIMITATION]})
    return output
