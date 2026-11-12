"""Deterministic operator memory restoration."""

from __future__ import annotations

from phase42_narrative_common import base_registry_id, deterministic_sentence, phase42_artifact, render_narrative_page, stable_row_id, top_deltas


def build_operator_memory_restore_registry(outputs: dict) -> dict:
    rows = []
    labels = ["last important operational shift", "largest tracked change", "last survivability context", "most recent workload context"]
    deltas = top_deltas(outputs, 4)
    for index, row in enumerate(deltas):
        rows.append(
            {
                "operator_memory_restore_id": stable_row_id("OMR", labels[index], row["metric"], row["lineage_index"]),
                "memory_prompt": labels[index],
                "restored_context": deterministic_sentence(row),
                "source_metric": row["metric"],
                "benchmark_run_id": row.get("benchmark_run_id"),
                "lineage_index": row["lineage_index"],
                "human_review_required": True,
            }
        )
    artifact = phase42_artifact("deterministic_operator_memory_restore_v1")
    artifact.update({"operator_memory_restore_registry_id": base_registry_id("OMRREG", rows, "operator_memory_restore_id"), "memory_items": rows, "summary": {"memory_item_count": len(rows)}})
    return artifact


def render_operator_memory_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("operator_memory_restore_registry") or {}).get("memory_items") or []
    return render_narrative_page("Operator Memory Dashboard", "operator_memory_dashboard.html", rows, ["memory_prompt", "restored_context", "source_metric"], "operator_memory_restore_id", [("Memory items", len(rows))])
