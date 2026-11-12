"""Deterministic historical scope narrowing."""

from __future__ import annotations

from phase44_wayfinding_common import focus_specs, path_for_focus, phase44_artifact, render_wayfinding_page, source_ids, stable_row_id


def build_historical_scope_registry(outputs: dict) -> dict:
    rows = []
    for focus, _keywords in focus_specs():
        events = path_for_focus(outputs, focus, 4)
        rows.append(
            {
                "historical_scope_id": stable_row_id("HSN", focus, source_ids(events)),
                "scope_type": f"{focus}_scope",
                "focus": focus,
                "included_event_ids": source_ids(events),
                "scope_rule": "highest_significance_then_stable_id",
                "scope_summary": f"{focus.title()} scope narrows recall to {len(events)} source events.",
                "human_review_required": True,
            }
        )
    artifact = phase44_artifact("deterministic_historical_scope_narrowing_v1")
    artifact.update({"historical_scope_registry_id": stable_row_id("HSNREG", [row["historical_scope_id"] for row in rows]), "scopes": rows, "summary": {"scope_count": len(rows)}})
    return artifact


def render_historical_scope_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("historical_scope_registry") or {}).get("scopes") or []
    return render_wayfinding_page("Historical Scope Dashboard", "historical_scope_dashboard.html", rows, ["scope_type", "scope_rule", "scope_summary"], "historical_scope_id", [("Scopes", len(rows))])
