"""Deterministic operational endurance summaries."""

from __future__ import annotations

from phase46_resilience_common import bounded_score, phase46_artifact, render_resilience_page, stable_row_id


def build_operational_endurance_registry(outputs: dict) -> dict:
    stress = (outputs.get("large_history_stress_registry") or {}).get("large_history_stress_cases") or []
    pagination = (outputs.get("pagination_endurance_registry") or {}).get("pagination_endurance_checks") or []
    deep_links = (outputs.get("deep_link_survivability_registry") or {}).get("deep_link_survivability_checks") or []
    rows = []
    scopes = [
        ("long_session_navigation", len(stress), sum(1 for row in stress if row.get("stress_status") == "survives")),
        ("pagination_endurance", len(pagination), sum(1 for row in pagination if row.get("endurance_status") == "survives")),
        ("deep_link_endurance", len(deep_links), sum(1 for row in deep_links if row.get("survivability_status") == "survives")),
    ]
    for scope, total, surviving in scopes:
        score = bounded_score(surviving, total)
        rows.append(
            {
                "operational_endurance_id": stable_row_id("OES", scope, total, surviving),
                "endurance_scope": scope,
                "checked_item_count": total,
                "surviving_item_count": surviving,
                "endurance_score": score,
                "endurance_status": "strong" if score >= 0.8 else "review",
                "human_review_required": True,
            }
        )
    artifact = phase46_artifact("deterministic_operational_endurance_summary_v1")
    artifact.update({"operational_endurance_registry_id": stable_row_id("OESREG", [row["operational_endurance_id"] for row in rows]), "operational_endurance_entries": rows, "summary": {"operational_endurance_entry_count": len(rows)}})
    return artifact


def render_operational_endurance_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("operational_endurance_registry") or {}).get("operational_endurance_entries") or []
    return render_resilience_page("Operational Endurance Dashboard", "operational_endurance_dashboard.html", rows, ["endurance_scope", "checked_item_count", "surviving_item_count", "endurance_score", "endurance_status"], "operational_endurance_id", [("Endurance entries", len(rows))])
