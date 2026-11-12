"""Deterministic longitudinal review bookmarks."""

from __future__ import annotations

from phase42_narrative_common import base_registry_id, phase42_artifact, render_narrative_page, stable_row_id, top_deltas


def build_longitudinal_review_bookmarks(outputs: dict) -> dict:
    rows = []
    for row in top_deltas(outputs, 8):
        rows.append(
            {
                "longitudinal_review_bookmark_id": stable_row_id("LRB", row["metric"], row["lineage_index"]),
                "bookmark_type": row["metric"],
                "bookmark_label": f"{row['label'].title()} {row['direction']}",
                "lineage_index": row["lineage_index"],
                "source_ref": row.get("benchmark_run_id"),
                "human_review_required": True,
            }
        )
    artifact = phase42_artifact("deterministic_longitudinal_review_bookmarks_v1")
    artifact.update({"longitudinal_review_bookmarks_id": base_registry_id("LRBREG", rows, "longitudinal_review_bookmark_id"), "bookmarks": rows, "summary": {"bookmark_count": len(rows)}})
    return artifact


def render_longitudinal_review_bookmarks_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("longitudinal_review_bookmarks") or {}).get("bookmarks") or []
    return render_narrative_page("Longitudinal Review Bookmarks Dashboard", "longitudinal_review_bookmarks_dashboard.html", rows, ["bookmark_type", "bookmark_label", "source_ref"], "longitudinal_review_bookmark_id", [("Bookmarks", len(rows))])
