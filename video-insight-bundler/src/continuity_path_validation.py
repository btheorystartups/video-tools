"""Deterministic continuity path validation."""

from __future__ import annotations

from phase44_wayfinding_common import event_id_set, graph_edges, phase44_artifact, render_wayfinding_page, stable_row_id


def build_continuity_path_validation_registry(outputs: dict) -> dict:
    valid_ids = event_id_set(outputs)
    rows = []
    for edge in graph_edges(outputs):
        missing = [node_id for node_id in [edge.get("from_node_id"), edge.get("to_node_id")] if node_id and node_id not in valid_ids]
        rows.append(
            {
                "continuity_path_validation_id": stable_row_id("CPV", edge.get("edge_id")),
                "edge_id": edge.get("edge_id"),
                "from_node_id": edge.get("from_node_id"),
                "to_node_id": edge.get("to_node_id"),
                "validation_status": "complete" if not missing else "error",
                "missing_node_ids": missing,
                "human_review_required": True,
            }
        )
    artifact = phase44_artifact("deterministic_continuity_path_validation_v1")
    artifact.update({"continuity_path_validation_registry_id": stable_row_id("CPVREG", [row["continuity_path_validation_id"] for row in rows]), "path_validations": rows, "summary": {"path_validation_count": len(rows), "invalid_path_count": len([row for row in rows if row["validation_status"] != "complete"])}})
    return artifact


def render_continuity_validation_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("continuity_path_validation_registry") or {}).get("path_validations") or []
    return render_wayfinding_page("Continuity Validation Dashboard", "continuity_validation_dashboard.html", rows, ["edge_id", "validation_status", "missing_node_ids"], "continuity_path_validation_id", [("Path validations", len(rows))])
