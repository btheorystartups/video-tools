"""Progressive disclosure plans for dense static review pages."""

from __future__ import annotations

from operator_workflow_common import ergonomics_links, phase40_artifact, render_registry_page, stable_row_id


def build_progressive_disclosure_registry(outputs: dict) -> dict:
    specs = [
        ("expandable_detail_sections", "evidence_and_rationale", "Show identifiers and compact status before details."),
        ("compact_evidence_cards", "evidence", "Group evidence references into short cards with detail links."),
        ("detail_on_demand", "dashboard_metrics", "Keep secondary metrics collapsed until selected."),
        ("layered_metric_visibility", "performance", "Show baseline and drift summaries before raw rows."),
        ("compact_recommendation_summaries", "recommendations", "Show action, reason, and governance status only."),
        ("collapsible_queue_regions", "queues", "Display chunk headers before queue item detail."),
    ]
    rows = []
    for order, (pattern, target, behavior) in enumerate(specs, 1):
        rows.append({
            "progressive_disclosure_id": stable_row_id("PDISC", pattern, target),
            "display_order": order,
            "pattern": pattern,
            "target_region": target,
            "default_state": "collapsed" if order > 1 else "summary_visible",
            "operator_behavior": behavior,
            "governance_visibility_preserved": True,
            "hidden_adaptive_behavior": False,
        })
    artifact = phase40_artifact("deterministic_progressive_disclosure_v1")
    artifact.update({"progressive_disclosure_registry_id": stable_row_id("PDISCREG", [row["progressive_disclosure_id"] for row in rows]), "disclosure_entries": rows, "summary": {"disclosure_entry_count": len(rows), "collapsed_by_default_count": sum(1 for row in rows if row["default_state"] == "collapsed")}})
    return artifact


def render_progressive_disclosure_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("progressive_disclosure_registry") or {}).get("disclosure_entries") or []
    return {"progressive_disclosure_dashboard.html": render_registry_page("Progressive Disclosure Dashboard", "Session Ergonomics", "progressive_disclosure_dashboard.html", rows, ["display_order", "pattern", "target_region", "default_state", "operator_behavior"], "progressive_disclosure_id", [("Disclosure entries", len(rows))], ergonomics_links(""))}
