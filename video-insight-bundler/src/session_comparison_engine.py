"""Session comparison engine for longitudinal operational runs."""

from __future__ import annotations

from phase41_longitudinal_common import latest_lineage_entries, phase41_artifact, render_longitudinal_page, stable_row_id


def build_session_comparison_registry(outputs: dict) -> dict:
    entries = latest_lineage_entries(outputs)
    pairs = list(zip(entries, entries[1:]))
    if not pairs and entries:
        pairs = [(entries[0], entries[0])]
    rows = []
    for previous, current in pairs:
        rows.append(
            {
                "session_comparison_id": stable_row_id("SCOMP", previous.get("benchmark_lineage_entry_id"), current.get("benchmark_lineage_entry_id")),
                "previous_benchmark_run_id": previous.get("benchmark_run_id"),
                "current_benchmark_run_id": current.get("benchmark_run_id"),
                "queue_delta": int(current.get("queue_total_count") or 0) - int(previous.get("queue_total_count") or 0),
                "artifact_delta": int(current.get("artifact_total_count") or 0) - int(previous.get("artifact_total_count") or 0),
                "rebuild_cost_delta": round(float(current.get("rebuild_timing_seconds") or 0) - float(previous.get("rebuild_timing_seconds") or 0), 3),
                "validation_cost_delta": round(float(current.get("validation_timing_seconds") or 0) - float(previous.get("validation_timing_seconds") or 0), 3),
                "operational_survivability_review_required": True,
            }
        )
    artifact = phase41_artifact("deterministic_session_comparison_engine_v1")
    artifact.update({"session_comparison_registry_id": stable_row_id("SCOMPREG", [row["session_comparison_id"] for row in rows]), "session_comparisons": rows, "summary": {"session_comparison_count": len(rows), "lineage_entry_count": len(entries)}})
    return artifact


def render_session_comparison_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("session_comparison_registry") or {}).get("session_comparisons") or []
    return render_longitudinal_page("Session Comparison Dashboard", "session_comparison_dashboard.html", rows, ["previous_benchmark_run_id", "current_benchmark_run_id", "queue_delta", "artifact_delta", "rebuild_cost_delta"], "session_comparison_id", [("Session comparisons", len(rows))])

