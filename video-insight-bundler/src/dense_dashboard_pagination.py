"""Pagination plans for dense local dashboards."""

from __future__ import annotations

from operator_workflow_common import phase40_artifact, stable_row_id


def build_dense_dashboard_pagination_registry(outputs: dict, page_size: int = 50) -> dict:
    specs = [
        ("review_queue", len((outputs.get("review_queue_registry") or {}).get("queue_items") or [])),
        ("queue_chunks", len((outputs.get("queue_chunking_registry") or {}).get("queue_chunks") or [])),
        ("benchmark_history", len((outputs.get("empirical_benchmark_history") or {}).get("benchmark_runs") or [])),
        ("attention_heatmap", len((outputs.get("operator_attention_heatmap_registry") or {}).get("attention_cells") or [])),
    ]
    rows = []
    for region, count in specs:
        pages = max(1, (count + page_size - 1) // page_size)
        rows.append({"pagination_id": stable_row_id("DPAGE", region, count, page_size), "dashboard_region": region, "item_count": count, "page_size": page_size, "page_count": pages, "deterministic_static_pagination": True})
    artifact = phase40_artifact("deterministic_dense_dashboard_pagination_v1")
    artifact.update({"dense_dashboard_pagination_registry_id": stable_row_id("DPAGEREG", [row["pagination_id"] for row in rows]), "pagination_entries": rows, "summary": {"pagination_entry_count": len(rows), "page_size": page_size}})
    return artifact
