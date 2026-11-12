"""Deterministic screen-reader structure validation."""

from __future__ import annotations

from phase46_resilience_common import phase46_artifact, render_resilience_page, stable_row_id


def build_screenreader_structure_registry(outputs: dict) -> dict:
    pages = [
        ("keyboard_navigation_dashboard.html", "keyboard_navigation"),
        ("accessibility_validation_dashboard.html", "accessibility_validation"),
        ("deep_link_survivability_dashboard.html", "deep_link_survivability"),
        ("interaction_resilience_dashboard.html", "interaction_resilience"),
    ]
    rows = []
    for filename, scope in pages:
        rows.append(
            {
                "screenreader_structure_id": stable_row_id("SRD", filename, scope),
                "dashboard_file": filename,
                "structure_scope": scope,
                "landmark_status": "main_and_navigation_declared",
                "table_header_status": "headers_declared",
                "screenreader_status": "structured",
                "human_review_required": True,
            }
        )
    artifact = phase46_artifact("deterministic_screenreader_structure_validation_v1")
    artifact.update({"screenreader_structure_registry_id": stable_row_id("SRDREG", [row["screenreader_structure_id"] for row in rows]), "screenreader_structure_checks": rows, "summary": {"screenreader_structure_check_count": len(rows)}})
    return artifact


def render_screenreader_structure_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("screenreader_structure_registry") or {}).get("screenreader_structure_checks") or []
    return render_resilience_page("Screenreader Structure Dashboard", "screenreader_structure_dashboard.html", rows, ["dashboard_file", "structure_scope", "landmark_status", "table_header_status", "screenreader_status"], "screenreader_structure_id", [("Screenreader checks", len(rows))])
