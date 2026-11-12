"""Deterministic operational throughput indicators."""

from __future__ import annotations

from phase45_interaction_common import all_interaction_events, phase45_artifact, render_interaction_page, route_rows, stable_row_id


def build_throughput_indicator_registry(outputs: dict) -> dict:
    events = all_interaction_events(outputs, 96)
    route_count = len(route_rows())
    repair_count = (outputs.get("continuity_repair_queue") or {}).get("summary", {}).get("continuity_repair_queue_count", 0)
    compression = (outputs.get("interaction_compression_registry") or {}).get("interaction_compression_entries") or []
    rows = [
        {
            "throughput_indicator_id": stable_row_id("TIND", "continuity_density", len(events)),
            "indicator_type": "continuity_density",
            "indicator_value": round(len(events) / max(1, route_count), 3),
            "indicator_summary": "Continuity events per static route.",
            "human_review_required": True,
        },
        {
            "throughput_indicator_id": stable_row_id("TIND", "queue_survivability", repair_count),
            "indicator_type": "queue_survivability",
            "indicator_value": max(0, route_count - repair_count),
            "indicator_summary": "Routes available after accounting for orphan repair pressure.",
            "human_review_required": True,
        },
        {
            "throughput_indicator_id": stable_row_id("TIND", "dashboard_compression", len(compression)),
            "indicator_type": "dashboard_compression",
            "indicator_value": len(compression),
            "indicator_summary": "Number of deterministic compression scopes.",
            "human_review_required": True,
        },
        {
            "throughput_indicator_id": stable_row_id("TIND", "navigation_complexity", route_count),
            "indicator_type": "navigation_complexity",
            "indicator_value": route_count,
            "indicator_summary": "Count of static dashboard route hops in the interaction layer.",
            "human_review_required": True,
        },
    ]
    artifact = phase45_artifact("deterministic_operational_throughput_indicators_v1")
    artifact.update({"throughput_indicator_registry_id": stable_row_id("TINDREG", [row["throughput_indicator_id"] for row in rows]), "throughput_indicators": rows, "summary": {"throughput_indicator_count": len(rows)}})
    return artifact


def render_throughput_indicator_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("throughput_indicator_registry") or {}).get("throughput_indicators") or []
    return render_interaction_page("Throughput Indicator Dashboard", "throughput_indicator_dashboard.html", rows, ["indicator_type", "indicator_value", "indicator_summary"], "throughput_indicator_id", [("Indicators", len(rows))])
