"""Deterministic operational-history compression registry."""

from __future__ import annotations

from phase42_narrative_common import base_registry_id, deterministic_sentence, phase42_artifact, render_narrative_page, stable_row_id, top_deltas


def build_history_compression_registry(outputs: dict) -> dict:
    rows = []
    for row in top_deltas(outputs, 10):
        rows.append(
            {
                "history_compression_id": stable_row_id("HCOMP", row["metric"], row["lineage_index"], row["delta"]),
                "compression_type": "top_lineage_delta",
                "source_metric": row["metric"],
                "compressed_text": deterministic_sentence(row),
                "source_value_delta": row["delta"],
                "human_review_required": True,
            }
        )
    artifact = phase42_artifact("deterministic_history_compression_engine_v1")
    artifact.update({"history_compression_registry_id": base_registry_id("HCOMPREG", rows, "history_compression_id"), "compression_entries": rows, "summary": {"history_compression_count": len(rows)}})
    return artifact


def render_history_compression_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("history_compression_registry") or {}).get("compression_entries") or []
    return render_narrative_page("History Compression Dashboard", "history_compression_dashboard.html", rows, ["compression_type", "source_metric", "compressed_text"], "history_compression_id", [("Compression entries", len(rows))])
