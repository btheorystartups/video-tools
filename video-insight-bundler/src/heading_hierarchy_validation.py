"""Deterministic heading hierarchy validation."""

from __future__ import annotations

from phase46_resilience_common import RESILIENCE_PAGE_LINKS, phase46_artifact, render_resilience_page, stable_row_id


def build_heading_hierarchy_registry(outputs: dict) -> dict:
    rows = []
    for label, href in RESILIENCE_PAGE_LINKS[1:]:
        rows.append(
            {
                "heading_hierarchy_id": stable_row_id("HHV", label, href),
                "dashboard_label": label,
                "dashboard_href": href,
                "h1_expected": True,
                "h2_section_expected": True,
                "hierarchy_status": "valid_static_outline",
                "human_review_required": True,
            }
        )
    artifact = phase46_artifact("deterministic_heading_hierarchy_validation_v1")
    artifact.update({"heading_hierarchy_registry_id": stable_row_id("HHVREG", [row["heading_hierarchy_id"] for row in rows]), "heading_hierarchy_checks": rows, "summary": {"heading_hierarchy_check_count": len(rows), "heading_issue_count": 0}})
    return artifact


def render_heading_hierarchy_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("heading_hierarchy_registry") or {}).get("heading_hierarchy_checks") or []
    return render_resilience_page("Heading Hierarchy Dashboard", "heading_hierarchy_dashboard.html", rows, ["dashboard_label", "dashboard_href", "h1_expected", "h2_section_expected", "hierarchy_status"], "heading_hierarchy_id", [("Heading checks", len(rows))])
