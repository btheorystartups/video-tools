"""Recommendation lineage from raw evidence to review status."""

from __future__ import annotations

from intelligence_common import base_artifact
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


def build_recommendation_lineage(traceability: dict) -> dict:
    rows = []
    for entry in traceability.get("traceability_entries") or []:
        missing = []
        if not entry.get("evidence_refs"):
            missing.append("evidence_refs")
        if not entry.get("source_metrics"):
            missing.append("source_metrics")
        if not entry.get("affected_segments"):
            missing.append("affected_segments")
        score = round(max(0.0, 1.0 - len(missing) * 0.25), 3)
        rows.append(
            {
                "lineage_id": deterministic_id("RECLIN", entry.get("recommendation_id")),
                "recommendation_id": entry.get("recommendation_id"),
                "raw_artifacts": entry.get("contributing_artifacts") or entry.get("evidence_refs") or [],
                "metric_sources": entry.get("source_metrics") or [],
                "threshold_sources": entry.get("triggering_thresholds") or [],
                "interpretation_sources": [entry.get("why_generated"), entry.get("what_evidence_supports_it")],
                "optimization_guidance_sources": [entry.get("lowest_risk_optimization_path")],
                "related_segments": entry.get("affected_segments") or [],
                "related_visualizations": ["visualizations/recommendation_traceability.html", "visualizations/temporal_evidence_index.html"],
                "governance_relevance": entry.get("severity"),
                "lineage_completeness_score": score,
                "missing_links": missing,
                "review_status": "human_review_required",
                "non_claim_limitation": LIMITATION,
            }
        )
    output = base_artifact(method="deterministic_recommendation_lineage_v1")
    output.update({"recommendation_lineage_id": deterministic_id("RECLINREG", [row["lineage_id"] for row in rows]), "lineage_items": rows, "summary": {"lineage_item_count": len(rows), "complete_lineage_count": sum(1 for row in rows if not row["missing_links"])}, "limitations": [LIMITATION]})
    return output

