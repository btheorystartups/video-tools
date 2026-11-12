"""Recommendation drawer models for static workstation pages."""

from __future__ import annotations

from intelligence_common import base_artifact
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


def build_recommendation_drawer_index(traceability: dict, lineage: dict, optimization_paths: dict) -> dict:
    lineage_ids = {row.get("recommendation_id"): row for row in lineage.get("lineage_items") or []}
    path_by_id = {row.get("recommendation_id"): row for row in optimization_paths.get("optimization_paths") or []}
    drawers = []
    for rec in traceability.get("traceability_entries") or []:
        first_segment = (rec.get("affected_segments") or [{}])[0]
        rec_id = rec.get("recommendation_id")
        drawers.append(
            {
                "drawer_id": deterministic_id("RCDRAW", rec_id),
                "recommendation_id": rec_id,
                "title": rec.get("title"),
                "affected_video": first_segment.get("source_video"),
                "affected_segment": first_segment.get("segment_id"),
                "severity": rec.get("severity"),
                "priority_score": rec.get("priority_score"),
                "effort_estimate": rec.get("effort_estimate"),
                "expected_benefit": rec.get("expected_benefit"),
                "evidence_summary": rec.get("what_evidence_supports_it"),
                "source_metrics": rec.get("source_metrics") or [],
                "optimization_path": (path_by_id.get(rec_id) or {}).get("lowest_risk_path") or rec.get("lowest_risk_optimization_path"),
                "risk_of_overcorrection": rec.get("risk_of_overcorrection"),
                "preserve_as_intentional_option": rec.get("preserve_as_intentional_option"),
                "human_review_requirement": "Human review is required before production or editorial changes.",
                "links": {
                    "lineage": "visualizations/recommendation_lineage.html",
                    "segment": f"visualizations/timeline/segment_context_{first_segment.get('video_id')}_{first_segment.get('segment_id')}.html",
                    "evidence": "visualizations/recommendation_evidence_map.html",
                    "governance": "visualizations/governance_diagnostics.html",
                    "compare": "visualizations/compare_workflows.html",
                },
                "lineage_completeness_score": (lineage_ids.get(rec_id) or {}).get("lineage_completeness_score"),
                "non_claim_limitation": LIMITATION,
            }
        )
    output = base_artifact(method="deterministic_recommendation_drawer_v1")
    output.update({"recommendation_drawer_index_id": deterministic_id("RCDRAWREG", [row["drawer_id"] for row in drawers]), "drawers": drawers, "summary": {"recommendation_drawer_count": len(drawers)}, "limitations": [LIMITATION]})
    return output
