"""Deterministic milestone continuity maps."""

from __future__ import annotations

from phase43_recall_common import phase43_artifact, render_recall_page, stable_row_id


def build_milestone_continuity_registry(outputs: dict) -> dict:
    milestones = (outputs.get("operational_milestone_registry") or {}).get("milestones") or []
    rows = []
    for index, item in enumerate(milestones):
        next_item = milestones[index + 1] if index + 1 < len(milestones) else None
        rows.append(
            {
                "milestone_continuity_id": stable_row_id("MCONT", item.get("operational_milestone_id"), next_item.get("operational_milestone_id") if next_item else "terminal"),
                "milestone_id": item.get("operational_milestone_id"),
                "next_milestone_id": next_item.get("operational_milestone_id") if next_item else None,
                "continuity_type": item.get("milestone_type"),
                "summary": item.get("description"),
                "human_review_required": True,
            }
        )
    artifact = phase43_artifact("deterministic_milestone_continuity_map_v1")
    artifact.update({"milestone_continuity_registry_id": stable_row_id("MCONTREG", [row["milestone_continuity_id"] for row in rows]), "milestone_paths": rows, "summary": {"milestone_continuity_count": len(rows)}})
    return artifact


def render_milestone_continuity_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("milestone_continuity_registry") or {}).get("milestone_paths") or []
    return render_recall_page("Milestone Continuity Dashboard", "milestone_continuity_dashboard.html", rows, ["continuity_type", "milestone_id", "next_milestone_id", "summary"], "milestone_continuity_id", [("Milestone links", len(rows))])
