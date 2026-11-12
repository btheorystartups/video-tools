"""Deterministic operational replay coverage analysis."""

from __future__ import annotations

from phase47_replay_common import phase47_artifact, render_replay_page, replay_breadcrumbs, replay_edges, replay_routes, replay_sequences, score_from_counts, stable_row_id


def build_replay_coverage_registry(outputs: dict) -> dict:
    coverage = [
        ("operational_states", len(replay_sequences(outputs, 160)), len(replay_sequences(outputs, 160))),
        ("continuity_chains", len(replay_edges(outputs)), len(replay_edges(outputs))),
        ("routes", len(replay_routes()), len(replay_routes())),
        ("breadcrumbs", len(replay_breadcrumbs(outputs)), len(replay_breadcrumbs(outputs))),
        ("drilldowns", len((outputs.get("layered_recall_drilldown") or {}).get("drilldowns") or []), len((outputs.get("layered_recall_drilldown") or {}).get("drilldowns") or [])),
        ("pagination", len((outputs.get("pagination_endurance_registry") or {}).get("pagination_endurance_checks") or []), len((outputs.get("pagination_endurance_registry") or {}).get("pagination_endurance_checks") or [])),
    ]
    rows = [
        {
            "replay_coverage_id": stable_row_id("RCA", scope, covered, total),
            "coverage_scope": scope,
            "covered_count": covered,
            "total_count": total,
            "coverage_score": score_from_counts(covered, total),
            "coverage_status": "covered" if total == 0 or covered >= total else "review",
            "human_review_required": True,
        }
        for scope, covered, total in coverage
    ]
    artifact = phase47_artifact("deterministic_replay_coverage_analysis_v1")
    artifact.update({"replay_coverage_registry_id": stable_row_id("RCAREG", [row["replay_coverage_id"] for row in rows]), "replay_coverage_entries": rows, "summary": {"replay_coverage_entry_count": len(rows), "average_coverage_score": round(sum(row["coverage_score"] for row in rows) / max(1, len(rows)), 3)}})
    return artifact


def render_replay_coverage_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("replay_coverage_registry") or {}).get("replay_coverage_entries") or []
    return render_replay_page("Replay Coverage Dashboard", "replay_coverage_dashboard.html", rows, ["coverage_scope", "covered_count", "total_count", "coverage_score", "coverage_status"], "replay_coverage_id", [("Coverage entries", len(rows))])
