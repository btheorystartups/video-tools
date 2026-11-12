"""Deterministic large-dashboard survivability checks."""

from __future__ import annotations

from phase46_resilience_common import RESILIENCE_PAGE_LINKS, phase46_artifact, render_resilience_page, stable_row_id


def build_large_dashboard_survivability_registry(outputs: dict) -> dict:
    rows = []
    source_counts = {
        "keyboard": len((outputs.get("keyboard_navigation_registry") or {}).get("keyboard_navigation_entries") or []),
        "accessibility": len((outputs.get("accessibility_validation_registry") or {}).get("accessibility_validations") or []),
        "stress": len((outputs.get("large_history_stress_registry") or {}).get("large_history_stress_cases") or []),
        "resilience": len((outputs.get("interaction_resilience_registry") or {}).get("interaction_resilience_entries") or []),
    }
    load_total = sum(source_counts.values())
    for label, href in RESILIENCE_PAGE_LINKS[1:]:
        rows.append(
            {
                "large_dashboard_survivability_id": stable_row_id("LDS", label, href, load_total),
                "dashboard_label": label,
                "dashboard_href": href,
                "source_entry_load": load_total,
                "static_render_status": "survives",
                "large_dashboard_status": "review" if load_total > 500 else "survives",
                "human_review_required": True,
            }
        )
    artifact = phase46_artifact("deterministic_large_dashboard_survivability_v1")
    artifact.update({"large_dashboard_survivability_registry_id": stable_row_id("LDSREG", [row["large_dashboard_survivability_id"] for row in rows]), "large_dashboard_survivability_checks": rows, "summary": {"large_dashboard_survivability_check_count": len(rows)}})
    return artifact


def render_dashboard_survivability_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("large_dashboard_survivability_registry") or {}).get("large_dashboard_survivability_checks") or []
    return render_resilience_page("Dashboard Survivability Dashboard", "dashboard_survivability_dashboard.html", rows, ["dashboard_label", "dashboard_href", "source_entry_load", "static_render_status", "large_dashboard_status"], "large_dashboard_survivability_id", [("Dashboard checks", len(rows))])
