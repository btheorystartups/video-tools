"""Deterministic historical significance registry."""

from __future__ import annotations

from phase42_narrative_common import base_registry_id, deterministic_sentence, phase42_artifact, render_narrative_page, stable_row_id, top_deltas


def build_historical_significance_registry(outputs: dict) -> dict:
    rows = []
    for rank, row in enumerate(top_deltas(outputs, 15), start=1):
        rows.append(
            {
                "historical_significance_id": stable_row_id("HSIG", rank, row["metric"], row["lineage_index"], row["delta"]),
                "rank": rank,
                "event_type": row["metric"],
                "lineage_index": row["lineage_index"],
                "benchmark_run_id": row.get("benchmark_run_id"),
                "event_summary": deterministic_sentence(row),
                "significance_score": row["significance_score"],
                "significance_level": row["significance_level"],
                "human_review_required": True,
            }
        )
    artifact = phase42_artifact("deterministic_historical_significance_v1")
    artifact.update({"historical_significance_registry_id": base_registry_id("HSIGREG", rows, "historical_significance_id"), "significance_events": rows, "summary": {"historical_significance_count": len(rows)}})
    return artifact


def render_historical_significance_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("historical_significance_registry") or {}).get("significance_events") or []
    return render_narrative_page("Historical Significance Dashboard", "historical_significance_dashboard.html", rows, ["rank", "event_type", "event_summary", "significance_level"], "historical_significance_id", [("Significant events", len(rows))])
