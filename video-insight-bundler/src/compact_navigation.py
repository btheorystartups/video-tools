"""Compact navigation modes for high-density operator dashboards."""

from __future__ import annotations

from operator_workflow_common import ergonomics_links, phase40_artifact, render_registry_page, stable_row_id


def build_compact_navigation_registry(outputs: dict) -> dict:
    specs = [
        ("queue_path", "Queue chunks", len((outputs.get("queue_chunking_registry") or {}).get("queue_chunks") or []), "chunk_index"),
        ("resume_path", "Resume points", len((outputs.get("session_focus_restore_registry") or {}).get("focus_restore_entries") or []), "last_position"),
        ("benchmark_path", "Benchmark drift", len((outputs.get("performance_drift_registry") or {}).get("drift_entries") or []), "drift_status"),
        ("attention_path", "Attention pressure", len((outputs.get("operator_attention_heatmap_registry") or {}).get("attention_cells") or []), "pressure_level"),
        ("disclosure_path", "Progressive sections", len((outputs.get("progressive_disclosure_registry") or {}).get("disclosure_entries") or []), "default_state"),
    ]
    rows = []
    for mode, label, count, primary in specs:
        rows.append({
            "compact_navigation_id": stable_row_id("CNAV", mode, count),
            "navigation_mode": mode,
            "label": label,
            "linked_entry_count": count,
            "primary_sort": primary,
            "default_density": "compact",
            "preserves_all_detail_links": True,
        })
    artifact = phase40_artifact("deterministic_compact_navigation_v1")
    artifact.update({"compact_navigation_registry_id": stable_row_id("CNAVREG", [row["compact_navigation_id"] for row in rows]), "navigation_modes": rows, "summary": {"navigation_mode_count": len(rows), "linked_entry_total": sum(row["linked_entry_count"] for row in rows)}})
    return artifact


def render_compact_navigation_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("compact_navigation_registry") or {}).get("navigation_modes") or []
    return {"compact_navigation_dashboard.html": render_registry_page("Compact Navigation Dashboard", "Session Ergonomics", "compact_navigation_dashboard.html", rows, ["navigation_mode", "label", "linked_entry_count", "primary_sort", "default_density"], "compact_navigation_id", [("Modes", len(rows))], ergonomics_links(""))}
