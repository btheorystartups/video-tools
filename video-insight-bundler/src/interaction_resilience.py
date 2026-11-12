"""Deterministic interaction resilience scoring."""

from __future__ import annotations

from phase46_resilience_common import bounded_score, phase46_artifact, render_resilience_page, stable_row_id


def build_interaction_resilience_registry(outputs: dict) -> dict:
    metrics = [
        ("traversal_complexity", len((outputs.get("accessibility_traversal_registry") or {}).get("accessibility_traversal_entries") or []), 32),
        ("continuity_density", len((outputs.get("continuity_route_stress_registry") or {}).get("continuity_route_stress_entries") or []), 48),
        ("route_survivability", len((outputs.get("deep_link_survivability_registry") or {}).get("deep_link_survivability_checks") or []), 64),
        ("pagination_burden", len((outputs.get("pagination_endurance_registry") or {}).get("pagination_endurance_checks") or []), 32),
        ("navigation_overload", len((outputs.get("navigation_fatigue_registry") or {}).get("navigation_fatigue_entries") or []), 16),
        ("interaction_endurance", len((outputs.get("operational_endurance_registry") or {}).get("operational_endurance_entries") or []), 16),
    ]
    rows = []
    for scope, load, capacity in metrics:
        score = bounded_score(capacity - min(load, capacity), capacity)
        rows.append(
            {
                "interaction_resilience_id": stable_row_id("IRS", scope, load, capacity),
                "resilience_scope": scope,
                "observed_load": load,
                "declared_capacity": capacity,
                "resilience_score": score,
                "resilience_status": "strong" if score >= 0.65 else "review",
                "human_review_required": True,
            }
        )
    artifact = phase46_artifact("deterministic_interaction_resilience_v1")
    artifact.update({"interaction_resilience_registry_id": stable_row_id("IRSREG", [row["interaction_resilience_id"] for row in rows]), "interaction_resilience_entries": rows, "summary": {"interaction_resilience_entry_count": len(rows), "resilience_review_count": sum(1 for row in rows if row["resilience_status"] == "review")}})
    return artifact


def render_interaction_resilience_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("interaction_resilience_registry") or {}).get("interaction_resilience_entries") or []
    return render_resilience_page("Interaction Resilience Dashboard", "interaction_resilience_dashboard.html", rows, ["resilience_scope", "observed_load", "declared_capacity", "resilience_score", "resilience_status"], "interaction_resilience_id", [("Resilience entries", len(rows))])
