"""Generated static context panels for timeline workstation pages."""

from __future__ import annotations

from intelligence_common import base_artifact
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


def build_persistent_context_registry(temporal_index: dict, traceability: dict, gatekeeper: dict | None = None, profile_packs: dict | None = None) -> dict:
    rec_by_segment = {}
    for rec in traceability.get("traceability_entries") or []:
        for segment in rec.get("affected_segments") or []:
            rec_by_segment.setdefault((segment.get("video_id"), segment.get("segment_id")), []).append(rec)
    panels = []
    for entry in temporal_index.get("temporal_evidence_entries") or []:
        recs = rec_by_segment.get((entry.get("video_id"), entry.get("segment_id")), [])
        panels.append(
            {
                "context_panel_id": deterministic_id("PCP", entry.get("video_id"), entry.get("segment_id")),
                "current_video": entry.get("source_video"),
                "video_id": entry.get("video_id"),
                "current_segment": entry.get("segment_id"),
                "current_recommendation": recs[0].get("recommendation_id") if recs else None,
                "current_severity": (entry.get("highest_severity_signal") or {}).get("severity"),
                "linked_evidence": entry.get("evidence_refs") or [],
                "linked_optimization_actions": [rec.get("lowest_risk_optimization_path") for rec in recs if rec.get("lowest_risk_optimization_path")],
                "governance_relevance": "blocker-linked" if entry.get("blockers") else "review-context",
                "benchmark_context": "local corpus profile benchmark context",
                "review_journey_step": "timeline region review",
                "non_claim_limitation": LIMITATION,
            }
        )
    output = base_artifact(method="deterministic_persistent_context_panel_v1")
    output.update({"persistent_context_registry_id": deterministic_id("PCPREG", [row["context_panel_id"] for row in panels]), "context_panels": panels, "summary": {"context_panel_count": len(panels)}, "limitations": [LIMITATION]})
    return output
