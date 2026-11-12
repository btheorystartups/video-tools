"""Deterministic contextual deep links."""

from __future__ import annotations

from phase44_wayfinding_common import focus_specs, path_for_focus, phase44_artifact, render_wayfinding_page, source_ids, stable_row_id


def build_contextual_deep_link_registry(outputs: dict) -> dict:
    rows = []
    for focus, _keywords in focus_specs():
        for event in path_for_focus(outputs, focus, 4):
            event_id = event.get("source_event_id")
            rows.append(
                {
                    "contextual_deep_link_id": stable_row_id("CDL", focus, event_id),
                    "link_type": f"{focus}_deep_link",
                    "target_event_id": event_id,
                    "target_fragment": f"#{focus}-{event_id}",
                    "source_event_ids": source_ids([event]),
                    "link_status": "complete",
                    "human_review_required": True,
                }
            )
    artifact = phase44_artifact("deterministic_contextual_deep_links_v1")
    artifact.update({"contextual_deep_link_registry_id": stable_row_id("CDLREG", [row["contextual_deep_link_id"] for row in rows]), "deep_links": rows, "summary": {"deep_link_count": len(rows)}})
    return artifact


def render_contextual_deep_link_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("contextual_deep_link_registry") or {}).get("deep_links") or []
    return render_wayfinding_page("Contextual Deep Link Dashboard", "contextual_deep_link_dashboard.html", rows, ["link_type", "target_event_id", "target_fragment", "link_status"], "contextual_deep_link_id", [("Deep links", len(rows))])
