"""Deterministic longitudinal review narratives."""

from __future__ import annotations

from phase42_narrative_common import base_registry_id, deterministic_sentence, phase42_artifact, render_narrative_page, stable_row_id, top_deltas


def build_longitudinal_review_narratives(outputs: dict) -> dict:
    rows = []
    for row in top_deltas(outputs, 10):
        narrative_type = "operational_shift" if row["direction"] != "held steady" else "operational_stability"
        rows.append(
            {
                "longitudinal_review_narrative_id": stable_row_id("LRN", row["metric"], row["lineage_index"], row["delta"]),
                "narrative_type": narrative_type,
                "lineage_index": row["lineage_index"],
                "benchmark_run_id": row.get("benchmark_run_id"),
                "metric": row["metric"],
                "summary": deterministic_sentence(row),
                "historical_significance": row["significance_level"],
                "human_review_required": True,
            }
        )
    artifact = phase42_artifact("deterministic_longitudinal_review_narratives_v1")
    artifact.update({"longitudinal_review_narratives_id": base_registry_id("LRNREG", rows, "longitudinal_review_narrative_id"), "narratives": rows, "summary": {"narrative_count": len(rows)}})
    return artifact


def render_longitudinal_review_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("longitudinal_review_narratives") or {}).get("narratives") or []
    return render_narrative_page("Longitudinal Review Dashboard", "longitudinal_review_dashboard.html", rows, ["narrative_type", "metric", "summary", "historical_significance"], "longitudinal_review_narrative_id", [("Narratives", len(rows))])
