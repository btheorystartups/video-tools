"""Deterministic operational breadcrumbs."""

from __future__ import annotations

from phase44_wayfinding_common import focus_specs, path_for_focus, phase44_artifact, render_wayfinding_page, source_ids, stable_row_id


def build_operational_breadcrumb_registry(outputs: dict) -> dict:
    rows = []
    for focus, _keywords in focus_specs():
        events = path_for_focus(outputs, focus, 5)
        crumbs = [{"position": index + 1, "event_id": event.get("source_event_id"), "label": event.get("source_type")} for index, event in enumerate(events)]
        rows.append(
            {
                "operational_breadcrumb_id": stable_row_id("OBR", focus, source_ids(events)),
                "breadcrumb_type": f"{focus}_continuity",
                "focus": focus,
                "breadcrumbs": crumbs,
                "trail_length": len(crumbs),
                "orientation_summary": f"{focus.title()} breadcrumb trail preserves {len(crumbs)} historical steps.",
                "human_review_required": True,
            }
        )
    artifact = phase44_artifact("deterministic_operational_breadcrumbs_v1")
    artifact.update({"operational_breadcrumb_registry_id": stable_row_id("OBRREG", [row["operational_breadcrumb_id"] for row in rows]), "breadcrumbs": rows, "summary": {"breadcrumb_count": len(rows)}})
    return artifact


def render_operational_breadcrumb_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("operational_breadcrumb_registry") or {}).get("breadcrumbs") or []
    return render_wayfinding_page("Operational Breadcrumb Dashboard", "operational_breadcrumb_dashboard.html", rows, ["breadcrumb_type", "trail_length", "orientation_summary"], "operational_breadcrumb_id", [("Breadcrumb trails", len(rows))])
