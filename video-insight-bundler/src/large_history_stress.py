"""Deterministic large-history stress simulation."""

from __future__ import annotations

from phase46_resilience_common import bounded_score, continuity_edge_count, phase46_artifact, render_resilience_page, resilience_events, route_count, stable_row_id


def build_large_history_stress_registry(outputs: dict) -> dict:
    event_count = len(resilience_events(outputs, 512))
    edges = continuity_edge_count(outputs)
    routes = route_count()
    simulations = [
        ("dense_dashboard_routing", routes * max(event_count, 1), 512),
        ("large_continuity_chains", edges, 256),
        ("heavy_pagination", event_count, 128),
        ("large_escalation_histories", len((outputs.get("escalation_trend_analysis") or {}).get("trend_points") or []), 128),
        ("large_governance_histories", len((outputs.get("governance_history") or {}).get("classification_history") or []), 64),
        ("graph_density_overload", edges + routes, 320),
    ]
    rows = []
    for scope, load_value, threshold in simulations:
        survivability = bounded_score(threshold - min(load_value, threshold), threshold)
        rows.append(
            {
                "large_history_stress_id": stable_row_id("LHS", scope, load_value, threshold),
                "stress_scope": scope,
                "simulated_load": load_value,
                "stress_threshold": threshold,
                "survivability_score": survivability,
                "stress_status": "review" if survivability < 0.25 else "survives",
                "human_review_required": True,
            }
        )
    artifact = phase46_artifact("deterministic_large_history_stress_v1")
    artifact.update({"large_history_stress_registry_id": stable_row_id("LHSREG", [row["large_history_stress_id"] for row in rows]), "large_history_stress_cases": rows, "summary": {"large_history_stress_case_count": len(rows), "stress_review_count": sum(1 for row in rows if row["stress_status"] == "review")}})
    return artifact


def render_large_history_stress_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("large_history_stress_registry") or {}).get("large_history_stress_cases") or []
    return render_resilience_page("Large History Stress Dashboard", "large_history_stress_dashboard.html", rows, ["stress_scope", "simulated_load", "stress_threshold", "survivability_score", "stress_status"], "large_history_stress_id", [("Stress cases", len(rows))])
