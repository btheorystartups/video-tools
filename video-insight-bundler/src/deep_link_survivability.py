"""Deterministic deep-link survivability validation."""

from __future__ import annotations

from phase46_resilience_common import phase46_artifact, render_resilience_page, stable_row_id


def build_deep_link_survivability_registry(outputs: dict) -> dict:
    links = (outputs.get("contextual_deep_link_registry") or {}).get("deep_links") or []
    breadcrumbs = (outputs.get("operational_breadcrumb_registry") or {}).get("breadcrumbs") or []
    valid_targets = {row.get("target_event_id") for row in links if row.get("target_event_id")}
    rows = []
    for link in links:
        fragment = str(link.get("target_fragment") or "")
        status = "survives" if fragment.startswith("#") and link.get("target_event_id") in valid_targets else "broken"
        rows.append(
            {
                "deep_link_survivability_id": stable_row_id("DLS", link.get("contextual_deep_link_id"), status),
                "source_deep_link_id": link.get("contextual_deep_link_id"),
                "target_event_id": link.get("target_event_id"),
                "target_fragment": fragment,
                "breadcrumb_reference_available": bool(breadcrumbs),
                "survivability_status": status,
                "human_review_required": True,
            }
        )
    artifact = phase46_artifact("deterministic_deep_link_survivability_v1")
    artifact.update({"deep_link_survivability_registry_id": stable_row_id("DLSREG", [row["deep_link_survivability_id"] for row in rows]), "deep_link_survivability_checks": rows, "summary": {"deep_link_survivability_check_count": len(rows), "broken_deep_link_count": sum(1 for row in rows if row["survivability_status"] == "broken")}})
    return artifact


def render_deep_link_survivability_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("deep_link_survivability_registry") or {}).get("deep_link_survivability_checks") or []
    return render_resilience_page("Deep Link Survivability Dashboard", "deep_link_survivability_dashboard.html", rows, ["source_deep_link_id", "target_event_id", "target_fragment", "breadcrumb_reference_available", "survivability_status"], "deep_link_survivability_id", [("Deep-link checks", len(rows))])
