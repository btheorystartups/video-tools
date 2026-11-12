"""Deterministic breadcrumb replay validation."""

from __future__ import annotations

from phase47_replay_common import phase47_artifact, render_replay_page, replay_breadcrumbs, stable_row_id


def build_breadcrumb_replay_registry(outputs: dict) -> dict:
    rows = []
    for trail in replay_breadcrumbs(outputs):
        crumbs = trail.get("breadcrumbs") or []
        rows.append(
            {
                "breadcrumb_replay_id": stable_row_id("BRP", trail.get("operational_breadcrumb_id"), len(crumbs)),
                "breadcrumb_ref": trail.get("operational_breadcrumb_id"),
                "focus": trail.get("focus"),
                "trail_length": len(crumbs),
                "first_event_id": crumbs[0].get("event_id") if crumbs else None,
                "last_event_id": crumbs[-1].get("event_id") if crumbs else None,
                "breadcrumb_replay_status": "replayable" if crumbs else "review",
                "human_review_required": True,
            }
        )
    artifact = phase47_artifact("deterministic_breadcrumb_replay_validation_v1")
    artifact.update({"breadcrumb_replay_registry_id": stable_row_id("BRPREG", [row["breadcrumb_replay_id"] for row in rows]), "breadcrumb_replay_entries": rows, "summary": {"breadcrumb_replay_entry_count": len(rows)}})
    return artifact


def render_breadcrumb_replay_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("breadcrumb_replay_registry") or {}).get("breadcrumb_replay_entries") or []
    return render_replay_page("Breadcrumb Replay Dashboard", "breadcrumb_replay_dashboard.html", rows, ["focus", "trail_length", "first_event_id", "last_event_id", "breadcrumb_replay_status"], "breadcrumb_replay_id", [("Breadcrumb replays", len(rows))])
