"""Deterministic what-changed and why summaries."""

from __future__ import annotations

from phase42_narrative_common import base_registry_id, phase42_artifact, reason_for_metric, render_narrative_page, stable_row_id, top_deltas


def build_change_explanation_registry(outputs: dict) -> dict:
    rows = []
    for row in top_deltas(outputs, 12):
        rows.append(
            {
                "change_explanation_id": stable_row_id("CEX", row["metric"], row["lineage_index"], row["delta"]),
                "change_type": row["metric"],
                "lineage_index": row["lineage_index"],
                "benchmark_run_id": row.get("benchmark_run_id"),
                "what_changed": f"{row['label'].title()} {row['direction']} by {row['delta']}.",
                "why_it_changed": reason_for_metric(row["metric"], row["direction"]),
                "evidence_metric": row["metric"],
                "current_value": row["current_value"],
                "previous_value": row["previous_value"],
                "autonomous_interpretation_used": False,
                "human_review_required": True,
            }
        )
    artifact = phase42_artifact("deterministic_change_explanation_engine_v1")
    artifact.update({"change_explanation_registry_id": base_registry_id("CEXREG", rows, "change_explanation_id"), "change_explanations": rows, "summary": {"change_explanation_count": len(rows)}})
    return artifact


def render_change_explanation_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("change_explanation_registry") or {}).get("change_explanations") or []
    return render_narrative_page("Change Explanation Dashboard", "change_explanation_dashboard.html", rows, ["change_type", "what_changed", "why_it_changed", "current_value", "previous_value"], "change_explanation_id", [("Explanations", len(rows))])
