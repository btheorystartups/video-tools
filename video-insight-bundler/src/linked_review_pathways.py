"""Deterministic linked operational review pathways."""

from __future__ import annotations

from phase45_interaction_common import focus_events, focus_specs, phase45_artifact, render_interaction_page, source_ids, stable_row_id


PATHWAY_TYPES = ["governance_first", "escalation_first", "survivability_first", "ambiguity_first"]


def build_linked_review_pathway_registry(outputs: dict) -> dict:
    rows = []
    for pathway_type in PATHWAY_TYPES:
        focus = pathway_type.replace("_first", "")
        events = focus_events(outputs, focus, 8)
        ids = source_ids(events)
        rows.append(
            {
                "linked_review_pathway_id": stable_row_id("LRP", pathway_type, ids),
                "pathway_type": pathway_type,
                "recommended_traversal_path": ids,
                "dashboard_sequence": ["dashboard_lenses_dashboard.html", "continuity_priority_dashboard.html", "linked_review_pathways_dashboard.html"],
                "pathway_status": "available" if ids else "needs_review",
                "human_review_required": True,
            }
        )
    artifact = phase45_artifact("deterministic_linked_review_pathways_v1")
    artifact.update({"linked_review_pathway_registry_id": stable_row_id("LRPREG", [row["linked_review_pathway_id"] for row in rows]), "linked_review_pathways": rows, "summary": {"linked_review_pathway_count": len(rows)}})
    return artifact


def render_linked_review_pathways_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("linked_review_pathway_registry") or {}).get("linked_review_pathways") or []
    return render_interaction_page("Linked Review Pathways Dashboard", "linked_review_pathways_dashboard.html", rows, ["pathway_type", "pathway_status", "recommended_traversal_path", "dashboard_sequence"], "linked_review_pathway_id", [("Pathways", len(rows))])
