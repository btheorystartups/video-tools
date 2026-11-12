"""Deterministic compressed history summaries."""

from __future__ import annotations

from phase42_narrative_common import base_registry_id, deterministic_sentence, phase42_artifact, render_narrative_page, stable_row_id, top_deltas


def build_compressed_history_summary(outputs: dict) -> dict:
    rows = []
    for row in top_deltas(outputs, 6):
        rows.append(
            {
                "compressed_history_item_id": stable_row_id("CHS", row["metric"], row["lineage_index"], row["delta"]),
                "summary_type": row["metric"],
                "compressed_summary": deterministic_sentence(row),
                "compression_basis": "top_abs_lineage_delta",
                "significance_score": row["significance_score"],
                "human_review_required": True,
            }
        )
    artifact = phase42_artifact("deterministic_compressed_history_summary_v1")
    artifact.update({"compressed_history_summary_id": base_registry_id("CHSREG", rows, "compressed_history_item_id"), "compressed_summaries": rows, "summary": {"compressed_summary_count": len(rows)}})
    return artifact


def render_compressed_history_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("compressed_history_summary") or {}).get("compressed_summaries") or []
    return render_narrative_page("Compressed History Dashboard", "compressed_history_dashboard.html", rows, ["summary_type", "compressed_summary", "significance_score"], "compressed_history_item_id", [("Compressed summaries", len(rows))])
