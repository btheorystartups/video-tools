"""Deterministic historical recall pathways."""

from __future__ import annotations

from phase43_recall_common import RECALL_LENSES, events_for_focus, phase43_artifact, render_recall_page, source_ids, stable_row_id


def build_historical_recall_paths(outputs: dict) -> dict:
    paths = []
    for focus, _keywords in RECALL_LENSES:
        events = events_for_focus(outputs, focus, 6)
        paths.append(
            {
                "historical_recall_path_id": stable_row_id("HRP", focus, source_ids(events)),
                "recall_type": f"{focus}_recall",
                "focus": focus,
                "entry_event_ids": source_ids(events),
                "entry_count": len(events),
                "highest_significance_level": events[0].get("significance_level") if events else "low",
                "navigation_prompt": f"Review {focus} history from the highest-significance deterministic source events.",
                "human_review_required": True,
            }
        )
    artifact = phase43_artifact("deterministic_historical_recall_paths_v1")
    artifact.update({"historical_recall_paths_id": stable_row_id("HRPREG", [row["historical_recall_path_id"] for row in paths]), "recall_paths": paths, "summary": {"recall_path_count": len(paths)}})
    return artifact


def render_historical_recall_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("historical_recall_paths") or {}).get("recall_paths") or []
    return render_recall_page("Historical Recall Dashboard", "historical_recall_dashboard.html", rows, ["recall_type", "entry_count", "highest_significance_level", "navigation_prompt"], "historical_recall_path_id", [("Recall paths", len(rows))])
