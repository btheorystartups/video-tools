"""Deterministic review bookmark registry."""

from __future__ import annotations

from operator_workflow_common import phase40_artifact, stable_row_id


def build_review_bookmark_registry(outputs: dict) -> dict:
    bookmarks = []
    for source, rows, href in [
        ("review_queue", (outputs.get("review_queue_registry") or {}).get("queue_items") or [], "visualizations/review/review_queue_dashboard.html"),
        ("adjudication_queue", (outputs.get("adjudication_queue_registry") or {}).get("queue_items") or [], "visualizations/adjudication/adjudication_queue_dashboard.html"),
        ("queue_chunk", (outputs.get("queue_chunking_registry") or {}).get("queue_chunks") or [], "visualizations/ergonomics/queue_chunking_dashboard.html"),
    ]:
        for index, row in enumerate(rows[:12], 1):
            ref = row.get("queue_item_id") or row.get("item_id") or row.get("queue_chunk_id") or index
            bookmarks.append({
                "review_bookmark_id": stable_row_id("RBMK", source, ref),
                "source": source,
                "target_ref": ref,
                "bookmark_label": f"{source}:{index}",
                "restore_href": href,
                "deterministic_bookmark": True,
            })
    artifact = phase40_artifact("deterministic_review_bookmarks_v1")
    artifact.update({"review_bookmark_registry_id": stable_row_id("RBMKREG", [row["review_bookmark_id"] for row in bookmarks]), "bookmarks": bookmarks, "summary": {"bookmark_count": len(bookmarks)}})
    return artifact
