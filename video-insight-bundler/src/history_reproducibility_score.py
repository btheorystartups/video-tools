"""Deterministic large-history reproducibility scoring."""

from __future__ import annotations

from phase47_replay_common import phase47_artifact, render_replay_page, score_from_counts, stable_row_id


def build_history_reproducibility_registry(outputs: dict) -> dict:
    extreme = (outputs.get("extreme_history_registry") or {}).get("extreme_history_entries") or []
    graph = (outputs.get("large_scale_continuity_registry") or {}).get("large_scale_continuity_entries") or []
    coverage = (outputs.get("replay_coverage_registry") or {}).get("replay_coverage_entries") or []
    rows = [
        {"score_scope": "extreme_history", "input_count": len(extreme), "score": score_from_counts(len(extreme), len(extreme))},
        {"score_scope": "large_continuity_graph", "input_count": len(graph), "score": score_from_counts(len(graph), len(graph))},
        {"score_scope": "replay_coverage", "input_count": len(coverage), "score": round(sum(row.get("coverage_score") or 0 for row in coverage) / max(1, len(coverage)), 3)},
    ]
    for row in rows:
        row.update({"history_reproducibility_id": stable_row_id("HRS", row["score_scope"], row["input_count"], row["score"]), "reproducibility_status": "reproducible" if row["score"] >= 0.8 else "review", "human_review_required": True})
    artifact = phase47_artifact("deterministic_history_reproducibility_score_v1")
    artifact.update({"history_reproducibility_registry_id": stable_row_id("HRSREG", [row["history_reproducibility_id"] for row in rows]), "history_reproducibility_entries": rows, "summary": {"history_reproducibility_entry_count": len(rows), "average_reproducibility_score": round(sum(row["score"] for row in rows) / max(1, len(rows)), 3)}})
    return artifact


def render_history_reproducibility_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("history_reproducibility_registry") or {}).get("history_reproducibility_entries") or []
    return render_replay_page("History Reproducibility Dashboard", "history_reproducibility_dashboard.html", rows, ["score_scope", "input_count", "score", "reproducibility_status"], "history_reproducibility_id", [("Reproducibility scores", len(rows))])
