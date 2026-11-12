"""Deterministic operational drift explanations."""

from __future__ import annotations

from phase42_narrative_common import base_registry_id, phase42_artifact, reason_for_metric, render_narrative_page, stable_row_id, top_deltas


def build_drift_explanation_registry(outputs: dict) -> dict:
    rows = []
    for row in top_deltas(outputs, 12):
        rows.append(
            {
                "drift_explanation_id": stable_row_id("DEX", row["metric"], row["lineage_index"], row["delta"]),
                "drift_type": row["metric"],
                "direction": row["direction"],
                "drift_summary": f"{row['label'].title()} drift {row['direction']} by {row['delta']}.",
                "drift_basis": reason_for_metric(row["metric"], row["direction"]),
                "significance_level": row["significance_level"],
                "human_review_required": True,
            }
        )
    artifact = phase42_artifact("deterministic_drift_explanation_system_v1")
    artifact.update({"drift_explanation_registry_id": base_registry_id("DEXREG", rows, "drift_explanation_id"), "drift_explanations": rows, "summary": {"drift_explanation_count": len(rows)}})
    return artifact


def render_drift_explanation_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("drift_explanation_registry") or {}).get("drift_explanations") or []
    return render_narrative_page("Drift Explanation Dashboard", "drift_explanation_dashboard.html", rows, ["drift_type", "direction", "drift_summary", "drift_basis"], "drift_explanation_id", [("Drift explanations", len(rows))])
