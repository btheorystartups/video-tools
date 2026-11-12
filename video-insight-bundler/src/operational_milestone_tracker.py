"""Deterministic operational milestone tracking."""

from __future__ import annotations

from phase42_narrative_common import base_registry_id, deterministic_sentence, phase42_artifact, render_narrative_page, stable_row_id, top_deltas


def build_operational_milestone_registry(outputs: dict) -> dict:
    rows = []
    for row in top_deltas(outputs, 12):
        if row["significance_score"] <= 0:
            continue
        rows.append(
            {
                "operational_milestone_id": stable_row_id("OMILE", row["metric"], row["lineage_index"], row["current_value"]),
                "milestone_type": f"{row['metric']}_{row['direction'].replace(' ', '_')}",
                "lineage_index": row["lineage_index"],
                "benchmark_run_id": row.get("benchmark_run_id"),
                "description": deterministic_sentence(row),
                "significance_score": row["significance_score"],
                "significance_level": row["significance_level"],
                "append_only_lineage_ref": row.get("benchmark_run_id"),
                "human_review_required": True,
            }
        )
    artifact = phase42_artifact("deterministic_operational_milestone_tracker_v1")
    artifact.update({"operational_milestone_registry_id": base_registry_id("OMILEREG", rows, "operational_milestone_id"), "milestones": rows, "summary": {"milestone_count": len(rows)}})
    return artifact


def render_operational_milestones_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("operational_milestone_registry") or {}).get("milestones") or []
    return render_narrative_page("Operational Milestones Dashboard", "operational_milestones_dashboard.html", rows, ["milestone_type", "description", "significance_score", "significance_level"], "operational_milestone_id", [("Milestones", len(rows))])
