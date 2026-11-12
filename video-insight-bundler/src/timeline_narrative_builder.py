"""Readable deterministic longitudinal timeline builder."""

from __future__ import annotations

from phase42_narrative_common import base_registry_id, deterministic_sentence, lineage_deltas, phase42_artifact, render_narrative_page, stable_row_id


def build_timeline_narrative_registry(outputs: dict) -> dict:
    rows = []
    for row in lineage_deltas(outputs):
        if row["lineage_index"] == 0 and row["current_value"] == 0:
            continue
        rows.append(
            {
                "timeline_narrative_id": stable_row_id("TLN", row["lineage_index"], row["metric"], row["current_value"]),
                "timeline_step": row["lineage_index"],
                "timeline_theme": row["metric"],
                "benchmark_run_id": row.get("benchmark_run_id"),
                "narrative": deterministic_sentence(row),
                "significance_level": row["significance_level"],
                "human_review_required": True,
            }
        )
    artifact = phase42_artifact("deterministic_timeline_narrative_builder_v1")
    artifact.update({"timeline_narrative_registry_id": base_registry_id("TLNREG", rows, "timeline_narrative_id"), "timeline_entries": rows, "summary": {"timeline_entry_count": len(rows)}})
    return artifact


def render_narrative_timeline_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("timeline_narrative_registry") or {}).get("timeline_entries") or []
    return render_narrative_page("Narrative Timeline Dashboard", "narrative_timeline_dashboard.html", rows, ["timeline_step", "timeline_theme", "narrative", "significance_level"], "timeline_narrative_id", [("Timeline entries", len(rows))])
