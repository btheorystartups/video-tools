"""Deterministic cross-session operational memory."""

from __future__ import annotations

from phase42_narrative_common import base_registry_id, deterministic_sentence, governance_rows, phase42_artifact, render_narrative_page, stable_row_id, top_deltas


def build_cross_session_memory_registry(outputs: dict) -> dict:
    rows = []
    for row in top_deltas(outputs, 5):
        rows.append(
            {
                "cross_session_memory_id": stable_row_id("CSM", row["metric"], row["lineage_index"]),
                "memory_type": "lineage_change",
                "remembered_context": deterministic_sentence(row),
                "source_ref": row.get("benchmark_run_id"),
                "human_review_required": True,
            }
        )
    for row in governance_rows(outputs)[:5]:
        rows.append(
            {
                "cross_session_memory_id": stable_row_id("CSM", row.get("governance_drift_id")),
                "memory_type": "governance_pressure",
                "remembered_context": f"Governance pressure marker {row.get('drift_type')} remains visible at count {row.get('current_count', 0)}.",
                "source_ref": row.get("governance_drift_id"),
                "human_review_required": True,
            }
        )
    artifact = phase42_artifact("deterministic_cross_session_memory_v1")
    artifact.update({"cross_session_memory_registry_id": base_registry_id("CSMREG", rows, "cross_session_memory_id"), "memory_entries": rows, "summary": {"cross_session_memory_count": len(rows)}})
    return artifact


def render_cross_session_memory_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("cross_session_memory_registry") or {}).get("memory_entries") or []
    return render_narrative_page("Cross-Session Memory Dashboard", "cross_session_memory_dashboard.html", rows, ["memory_type", "remembered_context", "source_ref"], "cross_session_memory_id", [("Memory entries", len(rows))])
